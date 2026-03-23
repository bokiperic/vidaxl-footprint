from __future__ import annotations
import datetime
from pydantic import BaseModel


class SourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    base_url: str
    region: str | None
    scraper_key: str
    is_active: bool
    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: int
    source_id: int
    external_id: str
    author: str | None
    rating: float | None
    title: str | None
    body: str | None
    review_date: datetime.date | None
    product_name: str | None
    product_category: str | None
    sentiment: str | None
    sentiment_score: float | None
    topics: list | None
    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: int
    source_id: int
    url: str
    title: str | None
    body: str | None
    author: str | None
    published_date: datetime.date | None
    sentiment: str | None
    sentiment_score: float | None
    topics: list | None
    model_config = {"from_attributes": True}


class ScrapeRunOut(BaseModel):
    id: int
    source_id: int
    started_at: datetime.datetime
    finished_at: datetime.datetime | None
    status: str
    items_scraped: int
    model_config = {"from_attributes": True}


class ScrapeRequest(BaseModel):
    sources: list[str] | None = None  # scraper keys, None = all active


class AnalysisRunRequest(BaseModel):
    pass


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
