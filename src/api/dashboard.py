from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Review, Source, AnalysisResult, AnalysisRun
from src.config import settings
from src.services.analysis_service import get_analysis_results
from src.services.review_service import get_review_stats

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    """KPI cards data."""
    stats = await get_review_stats(db)
    source_count = await db.scalar(select(func.count()).select_from(Source).where(Source.is_active.is_(True))) or 0
    stats["active_sources"] = source_count
    return stats


@router.get("/complaints")
async def complaints(db: AsyncSession = Depends(get_db)):
    """Top complaints with frequency and quotes."""
    results = await get_analysis_results(db, "top_complaints")
    if not results:
        return {"complaints": []}

    data = results[0].data
    complaint_list = data.get("complaints", [])

    # Enrich complaints missing source info by finding a matching review
    needs_enrichment = [c for c in complaint_list if not c.get("source_url")]
    if needs_enrichment:
        from sqlalchemy import String, type_coerce
        from sqlalchemy.orm import selectinload
        for c in needs_enrichment:
            theme_words = c.get("theme", "").lower().split()
            for word in theme_words:
                if len(word) < 4:
                    continue
                result = await db.execute(
                    select(Review)
                    .options(selectinload(Review.source))
                    .where(Review.topics.isnot(None))
                    .where(type_coerce(Review.topics, String).ilike(f"%{word}%"))
                    .limit(1)
                )
                review = result.scalars().first()
                if review and review.source:
                    c["source_name"] = review.source.name
                    c["source_url"] = review.source.base_url
                    break

    return {"complaints": complaint_list}


@router.get("/products")
async def products(db: AsyncSession = Depends(get_db)):
    """Best/worst rated products."""
    # Best products
    best = await db.execute(
        select(Review.product_name, func.avg(Review.rating).label("avg_rating"), func.count().label("count"))
        .where(Review.product_name.isnot(None), Review.rating.isnot(None))
        .group_by(Review.product_name)
        .having(func.count() >= 2)
        .order_by(func.avg(Review.rating).desc())
        .limit(10)
    )
    worst = await db.execute(
        select(Review.product_name, func.avg(Review.rating).label("avg_rating"), func.count().label("count"))
        .where(Review.product_name.isnot(None), Review.rating.isnot(None))
        .group_by(Review.product_name)
        .having(func.count() >= 2)
        .order_by(func.avg(Review.rating).asc())
        .limit(10)
    )
    best_rows = best.all()
    worst_rows = worst.all()

    if best_rows or worst_rows:
        return {
            "best": [{"product": r[0], "avg_rating": round(float(r[1]), 2), "review_count": r[2]} for r in best_rows],
            "worst": [{"product": r[0], "avg_rating": round(float(r[1]), 2), "review_count": r[2]} for r in worst_rows],
        }

    # Fallback mock data when no product-level reviews exist
    from src.analysis.mock import mock_best_products, mock_worst_products
    return {
        "best": mock_best_products(),
        "worst": mock_worst_products(),
    }


@router.get("/trends")
async def trends(db: AsyncSession = Depends(get_db)):
    """Time-series sentiment data for charts."""
    results = await get_analysis_results(db, "sentiment_summary")
    if results:
        return results[0].data

    # Fallback: compute from DB
    result = await db.execute(
        select(
            func.date_trunc("month", Review.review_date).label("month"),
            Review.sentiment,
            func.count().label("cnt"),
        )
        .where(Review.review_date.isnot(None), Review.sentiment.isnot(None))
        .group_by("month", Review.sentiment)
        .order_by("month")
    )
    monthly_map = {}
    for row in result.all():
        m = row.month.strftime("%Y-%m") if row.month else "unknown"
        if m not in monthly_map:
            monthly_map[m] = {"month": m, "positive": 0, "neutral": 0, "negative": 0}
        key = {"POS": "positive", "NEU": "neutral", "NEG": "negative"}.get(row.sentiment, "neutral")
        monthly_map[m][key] = row.cnt

    return {"monthly": list(monthly_map.values())}


@router.get("/sources")
async def sources(db: AsyncSession = Depends(get_db)):
    """Per-source breakdown."""
    result = await db.execute(
        select(
            Source.name,
            Source.region,
            func.count(Review.id).label("review_count"),
            func.avg(Review.rating).label("avg_rating"),
            func.avg(Review.sentiment_score).label("avg_sentiment"),
        )
        .outerjoin(Review, Review.source_id == Source.id)
        .where(Source.is_active.is_(True))
        .group_by(Source.id, Source.name, Source.region)
        .order_by(func.count(Review.id).desc())
    )
    return {
        "sources": [
            {
                "name": r[0],
                "region": r[1],
                "review_count": r[2],
                "avg_rating": round(float(r[3]), 2) if r[3] else None,
                "avg_sentiment": round(float(r[4]), 2) if r[4] else None,
            }
            for r in result.all()
        ]
    }


@router.get("/insights")
async def insights(db: AsyncSession = Depends(get_db)):
    """LLM-generated recommendations."""
    # Get insights
    insight_results = await get_analysis_results(db, "insight")
    trend_results = await get_analysis_results(db, "trend")

    return {
        "insights": insight_results[0].data if insight_results else {},
        "trends": trend_results[0].data if trend_results else {},
    }
