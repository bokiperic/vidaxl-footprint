from __future__ import annotations
import datetime
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, ScrapeRun, Review, Article
from src.scrapers import SCRAPER_REGISTRY
from src.scrapers.base import ScrapedReview, ScrapedArticle

logger = logging.getLogger(__name__)


async def run_scraper_for_source(db: AsyncSession, source: Source) -> ScrapeRun:
    """Run the registered scraper for a given source and upsert results."""
    scraper_cls = SCRAPER_REGISTRY.get(source.scraper_key)
    if not scraper_cls:
        raise ValueError(f"No scraper registered for key: {source.scraper_key}")

    # Get last cursor state
    last_run = await db.scalar(
        select(ScrapeRun)
        .where(ScrapeRun.source_id == source.id, ScrapeRun.status == "completed")
        .order_by(ScrapeRun.id.desc())
        .limit(1)
    )
    cursor_state = last_run.cursor_state if last_run else None

    # Create new run
    run = ScrapeRun(source_id=source.id, started_at=datetime.datetime.now(datetime.timezone.utc), status="running")
    db.add(run)
    await db.flush()

    scraper = scraper_cls(base_url=source.base_url, source_id=source.id)
    count = 0

    try:
        async for item in scraper.scrape(cursor_state):
            if isinstance(item, ScrapedReview):
                await _upsert_review(db, source.id, item)
            elif isinstance(item, ScrapedArticle):
                await _upsert_article(db, source.id, item)
            count += 1

            # Batch commit every 50 items
            if count % 50 == 0:
                await db.commit()

        run.status = "completed"
        run.items_scraped = count
        run.finished_at = datetime.datetime.now(datetime.timezone.utc)
        run.cursor_state = scraper.get_cursor_state()
        await db.commit()
        logger.info(f"Scrape completed: source={source.name}, items={count}")

    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.datetime.now(datetime.timezone.utc)
        run.items_scraped = count
        await db.commit()
        logger.error(f"Scrape failed for {source.name}: {e}")
        raise

    return run


async def _upsert_review(db: AsyncSession, source_id: int, item: ScrapedReview):
    stmt = insert(Review).values(
        source_id=source_id,
        external_id=item.external_id,
        author=item.author,
        rating=item.rating,
        title=item.title,
        body=item.body,
        review_date=item.review_date,
        product_name=item.product_name,
        product_category=item.product_category,
        raw_data=item.raw_data,
    ).on_conflict_do_update(
        constraint="uq_review_source_external",
        set_={
            "author": item.author,
            "rating": item.rating,
            "title": item.title,
            "body": item.body,
            "review_date": item.review_date,
            "product_name": item.product_name,
            "product_category": item.product_category,
            "raw_data": item.raw_data,
        },
    )
    await db.execute(stmt)


async def _upsert_article(db: AsyncSession, source_id: int, item: ScrapedArticle):
    stmt = insert(Article).values(
        source_id=source_id,
        external_id=item.external_id,
        url=item.url,
        title=item.title,
        body=item.body,
        author=item.author,
        published_date=item.published_date,
        raw_data=item.raw_data,
    ).on_conflict_do_update(
        constraint="uq_article_source_external",
        set_={
            "url": item.url,
            "title": item.title,
            "body": item.body,
            "author": item.author,
            "published_date": item.published_date,
            "raw_data": item.raw_data,
        },
    )
    await db.execute(stmt)


async def get_active_sources(db: AsyncSession, scraper_keys: list[str] | None = None) -> list[Source]:
    """Get active sources, optionally filtered by scraper key."""
    q = select(Source).where(Source.is_active.is_(True))
    if scraper_keys:
        q = q.where(Source.scraper_key.in_(scraper_keys))
    result = await db.execute(q)
    return list(result.scalars().all())
