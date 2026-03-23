from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AnalysisResult, AnalysisRun


async def get_latest_analysis(db: AsyncSession) -> AnalysisRun | None:
    return await db.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    )


async def get_analysis_results(db: AsyncSession, result_type: str | None = None) -> list[AnalysisResult]:
    """Get latest analysis results, optionally filtered by type."""
    latest = await get_latest_analysis(db)
    if not latest:
        return []

    q = select(AnalysisResult).where(AnalysisResult.analysis_run_id == latest.id)
    if result_type:
        q = q.where(AnalysisResult.result_type == result_type)

    result = await db.execute(q)
    return list(result.scalars().all())
