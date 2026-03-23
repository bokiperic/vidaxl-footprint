from __future__ import annotations
import abc
import dataclasses
import datetime
import logging
from typing import AsyncGenerator

import httpx
from aiolimiter import AsyncLimiter

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


@dataclasses.dataclass
class ScrapedReview:
    external_id: str
    author: str | None = None
    rating: float | None = None
    title: str | None = None
    body: str | None = None
    review_date: datetime.date | None = None
    product_name: str | None = None
    product_category: str | None = None
    raw_data: dict | None = None


@dataclasses.dataclass
class ScrapedArticle:
    external_id: str
    url: str
    title: str | None = None
    body: str | None = None
    author: str | None = None
    published_date: datetime.date | None = None
    raw_data: dict | None = None


class BaseScraper(abc.ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, base_url: str, source_id: int):
        self.base_url = base_url
        self.source_id = source_id
        self._limiter = AsyncLimiter(max_rate=2, time_period=1)  # 2 req/s
        self._cursor_state: dict = {}
        self._ua_index = 0

    def _get_headers(self) -> dict:
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def _fetch(self, url: str, client: httpx.AsyncClient) -> httpx.Response:
        async with self._limiter:
            logger.info(f"Fetching {url}")
            resp = await client.get(url, headers=self._get_headers(), follow_redirects=True, timeout=30.0)
            resp.raise_for_status()
            return resp

    @abc.abstractmethod
    async def scrape(self, cursor_state: dict | None = None) -> AsyncGenerator[ScrapedReview | ScrapedArticle, None]:
        yield  # type: ignore

    def get_cursor_state(self) -> dict:
        return self._cursor_state
