from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, async_session
from src.analysis.pipeline import run_analysis_pipeline
from src.security import require_api_key

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"], dependencies=[Depends(require_api_key)])


async def _run_analysis():
    async with async_session() as db:
        await run_analysis_pipeline(db)


@router.post("/run")
async def trigger_analysis(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger the analysis pipeline."""
    background_tasks.add_task(_run_analysis)
    return {"status": "started", "message": "Analysis pipeline started in background"}
