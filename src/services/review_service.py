from __future__ import annotations
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Review, Source


async def get_reviews(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source_id: int | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    sentiment: str | None = None,
    search: str | None = None,
) -> tuple[list[Review], int]:
    q = select(Review)
    count_q = select(func.count()).select_from(Review)

    filters = []
    if source_id:
        filters.append(Review.source_id == source_id)
    if min_rating is not None:
        filters.append(Review.rating >= min_rating)
    if max_rating is not None:
        filters.append(Review.rating <= max_rating)
    if sentiment:
        filters.append(Review.sentiment == sentiment)
    if search:
        like = f"%{search}%"
        filters.append(or_(Review.title.ilike(like), Review.body.ilike(like)))

    for f in filters:
        q = q.where(f)
        count_q = count_q.where(f)

    total = await db.scalar(count_q) or 0
    result = await db.execute(
        q.order_by(Review.review_date.desc().nullslast(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_review_stats(db: AsyncSession) -> dict:
    total = await db.scalar(select(func.count()).select_from(Review)) or 0
    avg_rating = await db.scalar(select(func.avg(Review.rating))) or 0
    avg_sentiment = await db.scalar(select(func.avg(Review.sentiment_score))) or 0

    sentiment_counts = {}
    for sent in ["POS", "NEU", "NEG"]:
        cnt = await db.scalar(select(func.count()).select_from(Review).where(Review.sentiment == sent)) or 0
        sentiment_counts[sent] = cnt

    source_counts_result = await db.execute(
        select(Source.name, func.count())
        .join(Review, Review.source_id == Source.id)
        .group_by(Source.name)
    )
    source_counts = {name: cnt for name, cnt in source_counts_result.all()}

    return {
        "total_reviews": total,
        "avg_rating": round(float(avg_rating), 2),
        "avg_sentiment_score": round(float(avg_sentiment), 2),
        "sentiment_counts": sentiment_counts,
        "source_counts": source_counts,
    }
