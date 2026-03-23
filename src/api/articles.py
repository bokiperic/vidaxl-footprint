from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Article
from src.schemas.common import ArticleOut

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get("")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count()).select_from(Article)) or 0
    result = await db.execute(
        select(Article)
        .order_by(Article.published_date.desc().nullslast(), Article.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    articles = result.scalars().all()
    return {
        "items": [ArticleOut.model_validate(a) for a in articles],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
