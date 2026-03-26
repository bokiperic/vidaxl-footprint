from __future__ import annotations
import datetime
import hashlib
import logging
from typing import AsyncGenerator

from src.config import settings
from src.scrapers.base import BaseScraper, ScrapedArticle, ScrapedReview
from src.scrapers.registry import register

logger = logging.getLogger(__name__)

REVIEW_DOMAINS = [
    "reddit.com",
    "sitejabber.com",
    "complaintsboard.com",
    "trustpilot.com",
    "consumeraffairs.com",
]

REVIEW_KEYWORDS = " review complaint experience problem"


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:16]


def _parse_date(date_str: str | None) -> datetime.date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str[:19], fmt[:19]).date()
        except ValueError:
            continue
    return None


def _mock_search_results() -> list[dict]:
    return [
        {
            "url": "https://www.reddit.com/r/fashion/comments/abc123/hunkemoller_review",
            "title": "My Hunkemöller shopping experience - worth it?",
            "content": "Just bought several items from Hunkemöller online. The lingerie quality is decent for the price, but sizing was a bit off. Had to return two bras. Customer service was helpful though.",
            "published_date": "2026-03-15",
        },
        {
            "url": "https://www.sitejabber.com/reviews/hunkemoller.com",
            "title": "Hunkemöller Reviews - Mixed Experiences",
            "content": "Mixed reviews from customers. Some love the designs and seasonal collections, while others report issues with delivery times and inconsistent sizing across different product lines.",
            "published_date": "2026-03-10",
        },
        {
            "url": "https://fashionmagazine.example.com/hunkemoller-spring-2026",
            "title": "Hunkemöller Spring 2026 Collection Launch",
            "content": "Hunkemöller has unveiled its Spring 2026 collection featuring sustainable fabrics and inclusive sizing. The brand continues to expand its presence across European markets.",
            "published_date": "2026-03-01",
        },
        {
            "url": "https://www.complaintsboard.com/hunkemoller-b12345",
            "title": "Hunkemöller delivery and refund issues",
            "content": "Ordered online two weeks ago, still no delivery. Customer service says it's been shipped but tracking shows no movement. Very frustrating experience.",
            "published_date": "2026-02-28",
        },
    ]


@register("tavily_search")
class TavilySearchScraper(BaseScraper):
    """Searches the web for brand mentions and news using Tavily API."""

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedArticle, None]:
        # Skip if last search was within 24h
        if cursor_state and cursor_state.get("last_search"):
            last = datetime.datetime.fromisoformat(cursor_state["last_search"])
            if (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds() < 86400:
                logger.info(f"Skipping Tavily search for source {self.source_id} — searched within 24h")
                self._cursor_state = cursor_state
                return

        query = self.base_url  # base_url stores the search query

        if settings.use_mock_search:
            logger.info(f"Using mock Tavily search for: {query}")
            results = _mock_search_results()
        else:
            logger.info(f"Running Tavily search: {query}")
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=20,
                include_raw_content=True,
            )
            results = response.get("results", [])

        for item in results:
            url = item.get("url", "")
            title = item.get("title")
            body = item.get("raw_content") or item.get("content", "")
            published = _parse_date(item.get("published_date"))

            yield ScrapedArticle(
                external_id=_url_hash(url),
                url=url,
                title=title,
                body=body,
                author=None,
                published_date=published,
            )

        self._cursor_state = {
            "last_search": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


@register("tavily_reviews")
class TavilyReviewSearchScraper(BaseScraper):
    """Searches review sites and forums for brand mentions using Tavily API."""

    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedReview, None]:
        if cursor_state and cursor_state.get("last_search"):
            last = datetime.datetime.fromisoformat(cursor_state["last_search"])
            if (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds() < 86400:
                logger.info(f"Skipping Tavily review search for source {self.source_id} — searched within 24h")
                self._cursor_state = cursor_state
                return

        query = self.base_url + REVIEW_KEYWORDS

        if settings.use_mock_search:
            logger.info(f"Using mock Tavily review search for: {query}")
            results = _mock_search_results()
        else:
            logger.info(f"Running Tavily review search: {query}")
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=20,
                include_raw_content=True,
                include_domains=REVIEW_DOMAINS,
            )
            results = response.get("results", [])

        for item in results:
            url = item.get("url", "")
            title = item.get("title")
            body = item.get("raw_content") or item.get("content", "")
            published = _parse_date(item.get("published_date"))

            yield ScrapedReview(
                external_id=_url_hash(url),
                author=None,
                rating=None,
                title=title,
                body=body,
                review_date=published,
                raw_data={"source_url": url},
            )

        self._cursor_state = {
            "last_search": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
