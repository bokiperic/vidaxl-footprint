from __future__ import annotations
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, async_session
from src.models import ScrapeRun, Source
from src.schemas.common import ScrapeRequest, ScrapeRunOut
from src.security import require_api_key
from src.services.scraper_service import get_active_sources, run_scraper_for_source

router = APIRouter(prefix="/api/v1/scrape", tags=["scraper"], dependencies=[Depends(require_api_key)])
logger = logging.getLogger(__name__)


async def _run_scrape_job(source_ids: list[int]):
    """Background task that runs scrapers."""
    async with async_session() as db:
        for sid in source_ids:
            source = await db.get(Source, sid)
            if not source:
                continue
            try:
                await run_scraper_for_source(db, source)
            except Exception as e:
                logger.error(f"Scraper failed for {source.name}: {e}")


@router.post("/run")
async def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger scraping for specified sources (or all active)."""
    sources = await get_active_sources(db, scraper_keys=req.sources)
    if not sources:
        return {"status": "no_sources", "message": "No matching active sources found"}

    source_ids = [s.id for s in sources]
    background_tasks.add_task(_run_scrape_job, source_ids)

    return {
        "status": "started",
        "sources": [{"id": s.id, "name": s.name, "scraper_key": s.scraper_key} for s in sources],
    }


@router.get("/runs", response_model=list[ScrapeRunOut])
async def list_scrape_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(limit)
    )
    return result.scalars().all()
