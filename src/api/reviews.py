from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.common import ReviewOut
from src.services.review_service import get_reviews, get_review_stats

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get("")
async def list_reviews(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=100),
    source_id: int | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    sentiment: str | None = None,
    search: str | None = Query(None, max_length=200),
    db: AsyncSession = Depends(get_db),
):
    reviews, total = await get_reviews(db, page, page_size, source_id, min_rating, max_rating, sentiment, search)
    return {
        "items": [ReviewOut.model_validate(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
async def review_stats(db: AsyncSession = Depends(get_db)):
    return await get_review_stats(db)
