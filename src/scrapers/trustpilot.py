from __future__ import annotations
import datetime
import hashlib
import json
import logging
import re
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedReview
from src.scrapers.registry import register

logger = logging.getLogger(__name__)


@register("trustpilot")
class TrustpilotScraper(BaseScraper):
    """Scrapes Trustpilot review pages for any VidaXL regional profile."""

    MAX_PAGES = 50  # safety limit

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedReview, None]:
        start_page = 1
        if cursor_state and "last_page" in cursor_state:
            start_page = 1  # always re-scrape from start for dedup-based incremental

        async with httpx.AsyncClient() as client:
            page = start_page
            while page <= self.MAX_PAGES:
                url = f"{self.base_url}?page={page}"
                try:
                    resp = await self._fetch(url, client)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        break
                    raise

                reviews = self._parse_page(resp.text, page)
                if not reviews:
                    break

                for review in reviews:
                    yield review

                page += 1

            self._cursor_state = {"last_page": page - 1}

    def _parse_page(self, html: str, page_num: int) -> list[ScrapedReview]:
        soup = BeautifulSoup(html, "lxml")
        reviews = []

        # Try JSON-LD structured data first (more reliable)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "LocalBusiness":
                    for r in data.get("review", []):
                        reviews.append(self._parse_jsonld_review(r))
                    if reviews:
                        return reviews
            except (json.JSONDecodeError, KeyError):
                continue

        # Fallback: parse HTML review cards
        review_cards = soup.select("article.paper_paper__1PY90") or soup.select("[data-service-review-card-paper]") or soup.select("div.review-card")

        # Broader fallback: look for any section with review-like structure
        if not review_cards:
            review_cards = soup.select("section.styles_reviewsContainer__3_GQw article") or soup.select("[class*='review']")

        for card in review_cards:
            review = self._parse_html_review(card, page_num)
            if review:
                reviews.append(review)

        return reviews

    def _parse_jsonld_review(self, data: dict) -> ScrapedReview:
        review_id = data.get("url", "") or hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
        rating_val = None
        if "reviewRating" in data:
            rating_val = float(data["reviewRating"].get("ratingValue", 0))

        date_str = data.get("datePublished", "")
        review_date = None
        if date_str:
            try:
                review_date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            except ValueError:
                pass

        return ScrapedReview(
            external_id=str(review_id),
            author=data.get("author", {}).get("name"),
            rating=rating_val,
            title=data.get("headline"),
            body=data.get("reviewBody"),
            review_date=review_date,
            raw_data=data,
        )

    def _parse_html_review(self, card, page_num: int) -> ScrapedReview | None:
        # Extract rating from star images or data attributes
        rating = None
        star_el = card.select_one("[data-service-review-rating]") or card.select_one("img[alt*='star']") or card.select_one("[class*='star']")
        if star_el:
            alt = star_el.get("alt", "") or star_el.get("data-service-review-rating", "")
            match = re.search(r"(\d)", str(alt))
            if match:
                rating = float(match.group(1))

        # Title
        title_el = card.select_one("h2") or card.select_one("[data-service-review-title-typography]") or card.select_one("[class*='title']")
        title = title_el.get_text(strip=True) if title_el else None

        # Body
        body_el = card.select_one("[data-service-review-text-typography]") or card.select_one("p")
        body = body_el.get_text(strip=True) if body_el else None

        if not title and not body:
            return None

        # Author
        author_el = card.select_one("[data-consumer-name-typography]") or card.select_one("[class*='consumer']")
        author = author_el.get_text(strip=True) if author_el else None

        # Date
        time_el = card.select_one("time")
        review_date = None
        if time_el and time_el.get("datetime"):
            try:
                review_date = datetime.datetime.fromisoformat(time_el["datetime"].replace("Z", "+00:00")).date()
            except ValueError:
                pass

        # Generate stable ID from content
        content = f"{title or ''}{body or ''}{author or ''}"
        ext_id = hashlib.md5(content.encode()).hexdigest()[:16]

        return ScrapedReview(
            external_id=ext_id,
            author=author,
            rating=rating,
            title=title,
            body=body,
            review_date=review_date,
        )
