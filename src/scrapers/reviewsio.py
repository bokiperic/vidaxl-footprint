from __future__ import annotations
import datetime
import hashlib
import json
import logging
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedReview
from src.scrapers.registry import register

logger = logging.getLogger(__name__)


@register("reviewsio")
class ReviewsIOScraper(BaseScraper):
    """Scrapes Reviews.io company review pages."""

    MAX_PAGES = 20

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedReview, None]:
        async with httpx.AsyncClient() as client:
            page = 1
            while page <= self.MAX_PAGES:
                url = f"{self.base_url}?page={page}"
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

        # Try JSON-LD first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "Review":
                            reviews.append(self._from_jsonld(item))
                elif isinstance(data, dict) and data.get("@type") == "Review":
                    reviews.append(self._from_jsonld(data))
            except (json.JSONDecodeError, KeyError):
                continue

        if reviews:
            return reviews

        # Fallback: HTML parsing
        for card in soup.select("[class*='ReviewCard']") or soup.select(".review-card") or soup.select("[itemtype*='Review']"):
            title_el = card.select_one("h3, h4, [class*='title']")
            body_el = card.select_one("p, [class*='body'], [class*='content']")
            author_el = card.select_one("[class*='author'], [class*='name']")

            title = title_el.get_text(strip=True) if title_el else None
            body = body_el.get_text(strip=True) if body_el else None

            if not title and not body:
                continue

            content = f"{title or ''}{body or ''}"
            ext_id = hashlib.md5(content.encode()).hexdigest()[:16]

            rating = None
            rating_el = card.select_one("[class*='star'], [class*='rating']")
            if rating_el:
                import re
                m = re.search(r"(\d(?:\.\d)?)", rating_el.get_text())
                if m:
                    rating = float(m.group(1))

            reviews.append(ScrapedReview(
                external_id=ext_id,
                author=author_el.get_text(strip=True) if author_el else None,
                rating=rating,
                title=title,
                body=body,
            ))

        return reviews

    def _from_jsonld(self, data: dict) -> ScrapedReview:
        review_date = None
        ds = data.get("datePublished", "")
        if ds:
            try:
                review_date = datetime.datetime.fromisoformat(ds.replace("Z", "+00:00")).date()
            except ValueError:
                pass

        rating = None
        if "reviewRating" in data:
            rating = float(data["reviewRating"].get("ratingValue", 0))

        content = json.dumps(data, sort_keys=True)
        ext_id = data.get("url") or hashlib.md5(content.encode()).hexdigest()[:16]

        return ScrapedReview(
            external_id=str(ext_id),
            author=data.get("author", {}).get("name") if isinstance(data.get("author"), dict) else data.get("author"),
            rating=rating,
            title=data.get("headline") or data.get("name"),
            body=data.get("reviewBody"),
            review_date=review_date,
            raw_data=data,
        )
