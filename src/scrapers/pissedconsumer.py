from __future__ import annotations
import datetime
import hashlib
import logging
import re
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedReview
from src.scrapers.registry import register

logger = logging.getLogger(__name__)


@register("pissedconsumer")
class PissedConsumerScraper(BaseScraper):
    """Scrapes PissedConsumer reviews."""

    MAX_PAGES = 30

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedReview, None]:
        async with httpx.AsyncClient() as client:
            page = 1
            while page <= self.MAX_PAGES:
                sep = "&" if "?" in self.base_url else "?"
                url = f"{self.base_url}{sep}page={page}"
                try:
                    resp = await self._fetch(url, client)
                except httpx.HTTPStatusError:
                    break

                reviews = self._parse_page(resp.text)
                if not reviews:
                    break

                for review in reviews:
                    yield review
                page += 1

            self._cursor_state = {"last_page": page - 1}

    def _parse_page(self, html: str) -> list[ScrapedReview]:
        soup = BeautifulSoup(html, "lxml")
        reviews = []

        cards = (
            soup.select("[class*='review-card']")
            or soup.select("article[class*='review']")
            or soup.select("[data-review-id]")
            or soup.select(".complaints-list .card")
        )

        for card in cards:
            title_el = card.select_one("h3 a, h2 a, [class*='title'] a, [class*='title']")
            body_el = card.select_one("[class*='description'], [class*='text'], p.review-text")

            title = title_el.get_text(strip=True) if title_el else None
            body = body_el.get_text(strip=True) if body_el else None

            if not title and not body:
                continue

            # Rating
            rating = None
            rating_el = card.select_one("[class*='star'], [class*='rating']")
            if rating_el:
                m = re.search(r"(\d(?:\.\d)?)", rating_el.get("title", "") or rating_el.get_text())
                if m:
                    rating = float(m.group(1))

            # Author
            author_el = card.select_one("[class*='author'], [class*='user']")
            author = author_el.get_text(strip=True) if author_el else None

            # Date
            date_el = card.select_one("time, [class*='date']")
            review_date = None
            if date_el:
                dt_str = date_el.get("datetime", "") or date_el.get_text(strip=True)
                try:
                    review_date = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()
                except ValueError:
                    m = re.search(r"(\w+ \d{1,2}, \d{4})", dt_str)
                    if m:
                        try:
                            review_date = datetime.datetime.strptime(m.group(1), "%B %d, %Y").date()
                        except ValueError:
                            pass

            ext_id = card.get("data-review-id") or hashlib.md5(f"{title or ''}{body or ''}".encode()).hexdigest()[:16]

            reviews.append(ScrapedReview(
                external_id=str(ext_id),
                author=author,
                rating=rating,
                title=title,
                body=body,
                review_date=review_date,
            ))

        return reviews
