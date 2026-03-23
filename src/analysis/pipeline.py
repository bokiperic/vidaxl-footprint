"""Analysis pipeline orchestrator."""
from __future__ import annotations
import datetime
import logging
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import AnalysisRun, AnalysisResult, Review, Source

logger = logging.getLogger(__name__)


async def run_analysis_pipeline(db: AsyncSession) -> AnalysisRun:
    """Run the full analysis pipeline (mock or Claude-powered)."""
    use_mock = settings.use_mock_analysis
    mode = "mock" if use_mock else "claude"

    run = AnalysisRun(started_at=datetime.datetime.now(datetime.timezone.utc), status="running", mode=mode)
    db.add(run)
    await db.flush()

    try:
        # Stage 1: Sentiment classification
        reviews_analyzed = await _stage1_sentiment(db, use_mock)
        run.reviews_analyzed = reviews_analyzed

        # Stage 2: Theme aggregation
        complaints = await _stage2_themes(db, run.id, use_mock)

        # Stage 3: Trends & insights
        await _stage3_trends(db, run.id, complaints, use_mock)

        run.status = "completed"
        run.finished_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
        logger.info(f"Analysis pipeline completed ({mode}): {reviews_analyzed} reviews")

    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
        logger.error(f"Analysis pipeline failed: {e}")
        raise

    return run


async def _stage1_sentiment(db: AsyncSession, use_mock: bool) -> int:
    """Classify sentiment for all unanalyzed reviews."""
    # Get reviews without sentiment
    result = await db.execute(
        select(Review).where(Review.sentiment.is_(None)).limit(1000)
    )
    reviews = list(result.scalars().all())

    if not reviews:
        return 0

    if use_mock:
        from src.analysis.mock import mock_sentiment
        for review in reviews:
            text = f"{review.title or ''} {review.body or ''}"
            sentiment, score, topics = mock_sentiment(text)
            review.sentiment = sentiment
            review.sentiment_score = score
            review.topics = topics
    else:
        from src.analysis.sentiment import classify_sentiment_batch
        review_dicts = [
            {"id": r.id, "title": r.title, "body": r.body, "rating": float(r.rating) if r.rating else None}
            for r in reviews
        ]
        results = await classify_sentiment_batch(review_dicts)
        result_map = {r["id"]: r for r in results}

        for review in reviews:
            if review.id in result_map:
                r = result_map[review.id]
                review.sentiment = r["sentiment"]
                review.sentiment_score = r["sentiment_score"]
                review.topics = r["topics"]

    await db.commit()
    return len(reviews)


async def _stage2_themes(db: AsyncSession, run_id: int, use_mock: bool) -> list[dict]:
    """Aggregate topics into complaint themes."""
    if use_mock:
        from src.analysis.mock import mock_top_complaints
        complaints = mock_top_complaints()
    else:
        # Aggregate topic frequencies from DB
        result = await db.execute(select(Review.topics).where(Review.topics.isnot(None)))
        all_topics = Counter()
        total = 0
        for (topics,) in result:
            if topics:
                for t in topics:
                    all_topics[t] += 1
                total += 1

        from src.analysis.themes import aggregate_themes
        complaints = await aggregate_themes(dict(all_topics), total)

    # Store result
    ar = AnalysisResult(
        analysis_run_id=run_id,
        result_type="top_complaints",
        title="Top Customer Complaints",
        data={"complaints": complaints},
    )
    db.add(ar)
    await db.flush()
    return complaints


async def _stage3_trends(db: AsyncSession, run_id: int, complaints: list[dict], use_mock: bool):
    """Detect trends and generate insights."""
    if use_mock:
        from src.analysis.mock import mock_trends, mock_monthly_sentiment
        trends_data = mock_trends()
        monthly = mock_monthly_sentiment()
    else:
        # Build monthly sentiment data from DB
        result = await db.execute(
            select(
                func.date_trunc("month", Review.review_date).label("month"),
                Review.sentiment,
                func.count().label("cnt"),
                func.avg(Review.sentiment_score).label("avg_score"),
            )
            .where(Review.review_date.isnot(None), Review.sentiment.isnot(None))
            .group_by("month", Review.sentiment)
            .order_by("month")
        )
        rows = result.all()

        # Reshape into monthly buckets
        monthly_map = {}
        for row in rows:
            m = row.month.strftime("%Y-%m") if row.month else "unknown"
            if m not in monthly_map:
                monthly_map[m] = {"month": m, "positive": 0, "neutral": 0, "negative": 0, "avg_score": 0}
            key = {"POS": "positive", "NEU": "neutral", "NEG": "negative"}.get(row.sentiment, "neutral")
            monthly_map[m][key] = row.cnt
            monthly_map[m]["avg_score"] = round(float(row.avg_score or 0), 2)
        monthly = list(monthly_map.values())

        # Get aggregate stats
        stats = await db.execute(select(func.count(), func.avg(Review.rating)).select_from(Review))
        total_reviews, avg_rating = stats.one()

        sources_result = await db.execute(select(Source.name).where(Source.is_active.is_(True)))
        source_names = [r[0] for r in sources_result.all()]

        from src.analysis.trends import detect_trends
        trends_data = await detect_trends(monthly, complaints, total_reviews or 0, float(avg_rating or 0), source_names)

    # Store monthly sentiment for charts
    db.add(AnalysisResult(
        analysis_run_id=run_id,
        result_type="sentiment_summary",
        title="Monthly Sentiment Data",
        data={"monthly": monthly},
    ))

    # Store trends
    if trends_data.get("trends"):
        db.add(AnalysisResult(
            analysis_run_id=run_id,
            result_type="trend",
            title="Detected Trends",
            data={"trends": trends_data.get("trends", []), "seasonal_patterns": trends_data.get("seasonal_patterns", "")},
        ))

    # Store insights/recommendations
    if trends_data.get("recommendations"):
        db.add(AnalysisResult(
            analysis_run_id=run_id,
            result_type="insight",
            title="Actionable Insights",
            data={
                "recommendations": trends_data.get("recommendations", []),
                "source_specific": trends_data.get("source_specific", ""),
            },
        ))

    await db.flush()
