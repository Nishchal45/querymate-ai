"""Query history endpoints — view and manage past queries."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import HistoryItem, HistoryResponse
from backend.core.database import get_db
from backend.models.query_history import QueryHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/history', tags=['history'])


@router.get('', response_model=HistoryResponse)
async def list_history(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    """List query history with pagination and optional search."""
    query = select(QueryHistory).order_by(QueryHistory.created_at.desc())
    count_query = select(func.count()).select_from(QueryHistory)

    if search:
        query = query.where(
            QueryHistory.natural_language.ilike(f'%{search}%')
        )
        count_query = count_query.where(
            QueryHistory.natural_language.ilike(f'%{search}%')
        )

    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    return HistoryResponse(
        items=[
            HistoryItem(
                id=row.id,
                natural_language=row.natural_language,
                generated_sql=row.generated_sql,
                execution_time_ms=row.execution_time_ms,
                row_count=row.row_count,
                was_cached=row.was_cached,
                cache_level=row.cache_level,
                error=row.error,
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete('')
async def clear_history(db: AsyncSession = Depends(get_db)) -> dict:
    """Clear all query history."""
    from sqlalchemy import delete

    await db.execute(delete(QueryHistory))
    await db.commit()
    logger.info('Query history cleared')
    return {'message': 'History cleared'}
