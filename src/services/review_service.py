from __future__ import annotations
from datetime import date
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    start_date: date | None = None,
    end_date: date | None = None,
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
    if start_date is not None:
        filters.append(Review.review_date >= start_date)
    if end_date is not None:
        filters.append(Review.review_date <= end_date)

    for f in filters:
        q = q.where(f)
        count_q = count_q.where(f)

    total = await db.scalar(count_q) or 0
    result = await db.execute(
        q.options(selectinload(Review.source))
        .order_by(Review.review_date.desc().nullslast(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


def _date_filters(start_date: date | None, end_date: date | None) -> list:
    filters = []
    if start_date is not None:
        filters.append(Review.review_date >= start_date)
    if end_date is not None:
        filters.append(Review.review_date <= end_date)
    return filters


async def get_review_stats(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    df = _date_filters(start_date, end_date)

    base = select(func.count()).select_from(Review)
    for f in df:
        base = base.where(f)
    total = await db.scalar(base) or 0

    avg_q = select(func.avg(Review.rating)).select_from(Review)
    for f in df:
        avg_q = avg_q.where(f)
    avg_rating = await db.scalar(avg_q) or 0

    sent_q = select(func.avg(Review.sentiment_score)).select_from(Review)
    for f in df:
        sent_q = sent_q.where(f)
    avg_sentiment = await db.scalar(sent_q) or 0

    sentiment_counts = {}
    for sent in ["POS", "NEU", "NEG"]:
        q = select(func.count()).select_from(Review).where(Review.sentiment == sent)
        for f in df:
            q = q.where(f)
        cnt = await db.scalar(q) or 0
        sentiment_counts[sent] = cnt

    src_q = (
        select(Source.name, func.count())
        .join(Review, Review.source_id == Source.id)
    )
    for f in df:
        src_q = src_q.where(f)
    src_q = src_q.group_by(Source.name)
    source_counts_result = await db.execute(src_q)
    source_counts = {name: cnt for name, cnt in source_counts_result.all()}

    return {
        "total_reviews": total,
        "avg_rating": round(float(avg_rating), 2),
        "avg_sentiment_score": round(float(avg_sentiment), 2),
        "sentiment_counts": sentiment_counts,
        "source_counts": source_counts,
    }
