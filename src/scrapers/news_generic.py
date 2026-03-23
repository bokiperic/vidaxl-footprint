from __future__ import annotations
import datetime
import hashlib
import logging
import re
from typing import AsyncGenerator
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedArticle
from src.scrapers.registry import register

logger = logging.getLogger(__name__)


@register("news_generic")
class NewsGenericScraper(BaseScraper):
    """Scrapes news articles via RSS feeds or HTML blog pages."""

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedArticle, None]:
        async with httpx.AsyncClient() as client:
            # Try RSS first
            rss_urls = [
                self.base_url + "/feed",
                self.base_url + "/rss",
                self.base_url + "/feed.xml",
            ]
            for rss_url in rss_urls:
                try:
                    resp = await self._fetch(rss_url, client)
                    if "xml" in resp.headers.get("content-type", ""):
                        async for article in self._parse_rss(resp.text):
                            yield article
                        return
                except (httpx.HTTPStatusError, Exception):
                    continue

            # Fallback: scrape HTML blog page
            try:
                resp = await self._fetch(self.base_url, client)
                async for article in self._parse_blog_html(resp.text, client):
                    yield article
            except httpx.HTTPStatusError:
                logger.warning(f"Could not scrape {self.base_url}")

    async def _parse_rss(self, xml_text: str) -> AsyncGenerator[ScrapedArticle, None]:
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for item in items:
            title = self._find_text(item, ["title", "atom:title"], ns)
            link = self._find_text(item, ["link", "atom:link"], ns)
            if not link:
                link_el = item.find("atom:link", ns)
                if link_el is not None:
                    link = link_el.get("href", "")
            desc = self._find_text(item, ["description", "atom:summary", "atom:content", "content:encoded"], ns)
            pub_date = self._find_text(item, ["pubDate", "atom:published", "atom:updated"], ns)
            author = self._find_text(item, ["author", "dc:creator", "atom:author/atom:name"], ns)

            if not title and not desc:
                continue

            ext_id = link or hashlib.md5((title or "").encode()).hexdigest()[:16]
            review_date = self._parse_date(pub_date) if pub_date else None

            # Strip HTML from description
            if desc:
                desc = BeautifulSoup(desc, "lxml").get_text(strip=True)

            yield ScrapedArticle(
                external_id=str(ext_id),
                url=link or self.base_url,
                title=title,
                body=desc,
                author=author,
                published_date=review_date,
            )

    async def _parse_blog_html(self, html: str, client: httpx.AsyncClient) -> AsyncGenerator[ScrapedArticle, None]:
        soup = BeautifulSoup(html, "lxml")
        articles = soup.select("article") or soup.select("[class*='post']") or soup.select("[class*='blog']")

        for article in articles[:20]:  # limit
            link_el = article.select_one("a[href]")
            title_el = article.select_one("h2, h3, h1, [class*='title']")

            title = title_el.get_text(strip=True) if title_el else None
            url = link_el["href"] if link_el else None

            if not url:
                continue

            if not url.startswith("http"):
                from urllib.parse import urljoin
                url = urljoin(self.base_url, url)

            ext_id = url or hashlib.md5((title or "").encode()).hexdigest()[:16]

            yield ScrapedArticle(
                external_id=str(ext_id),
                url=url,
                title=title,
                body=None,  # Could fetch full article content if needed
            )

    def _find_text(self, el, tags: list[str], ns: dict) -> str | None:
        for tag in tags:
            found = el.find(tag, ns) if ":" in tag else el.find(tag)
            if found is not None and found.text:
                return found.text.strip()
        return None

    def _parse_date(self, date_str: str) -> datetime.date | None:
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
        ]:
            try:
                return datetime.datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None
