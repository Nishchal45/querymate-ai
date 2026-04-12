"""Query endpoint — the main orchestrator that ties all services together.

Flow:
  1. Normalize question → check L1 cache
  2. If L1 miss: introspect schema → call LLM → validate SQL → cache in L1
  3. Check L2 cache with the SQL
  4. If L2 miss: execute query → cache results in L2
  5. Save to history (async, non-blocking)
  6. Return response
"""

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import QueryRequest, QueryResponse
from backend.core.database import async_session
from backend.models.query_history import QueryHistory
from backend.services import cache_service
from backend.services.introspector import introspect_schema
from backend.services.llm_service import generate_sql
from backend.services.query_executor import QueryError, QueryResult, execute_query
from backend.services.sql_validator import validate_sql

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['query'])


async def _save_history(
    query_id: uuid.UUID,
    question: str,
    sql: str,
    execution_time_ms: float,
    row_count: int | None,
    was_cached: bool,
    cache_level: str | None,
    error: str | None,
) -> None:
    """Save query to history (best-effort, non-blocking)."""
    try:
        async with async_session() as session:
            record = QueryHistory(
                id=query_id,
                natural_language=question,
                generated_sql=sql,
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                was_cached=was_cached,
                cache_level=cache_level,
                error=error,
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.warning('Failed to save query history: %s', e)


@router.post('/query', response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Execute a natural language query against the target database."""
    start = time.perf_counter()
    query_id = uuid.uuid4()
    question = request.question
    sql = ''
    cache_level = None
    was_cached = False

    try:
        # Step 1: Check L1 cache (NL → SQL)
        cached_sql = await cache_service.get_cached_sql(question)
        if cached_sql is not None:
            sql = cached_sql
            cache_level = 'L1'
        else:
            # Step 2: Introspect schema → generate SQL
            schema = introspect_schema()
            sql = await generate_sql(question, schema)

            # Step 3: Validate SQL
            validation = validate_sql(sql)
            if not validation.is_valid:
                elapsed = (time.perf_counter() - start) * 1000
                await _save_history(
                    query_id, question, sql, elapsed, None, False, None,
                    '; '.join(validation.violations),
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        'message': 'Query blocked by security validator',
                        'violations': validation.violations,
                        'sql': sql,
                    },
                )

            # Cache NL → SQL in L1
            await cache_service.set_cached_sql(question, sql)

        # Step 4: Check L2 cache (SQL → Results)
        cached_result = await cache_service.get_cached_result(sql)
        if cached_result is not None:
            was_cached = True
            if cache_level == 'L1':
                cache_level = 'L1+L2'
            else:
                cache_level = 'L2'

            elapsed = (time.perf_counter() - start) * 1000
            await _save_history(
                query_id, question, sql, elapsed,
                cached_result.row_count, True, cache_level, None,
            )
            return QueryResponse(
                query_id=query_id,
                question=question,
                sql=sql,
                result=cached_result.model_dump(),
                execution_time_ms=round(elapsed, 2),
                cached=True,
                cache_level=cache_level,
            )

        # Step 5: Execute query
        result = execute_query(sql)

        if isinstance(result, QueryError):
            elapsed = (time.perf_counter() - start) * 1000
            await _save_history(
                query_id, question, sql, elapsed, None, False, None,
                result.message,
            )
            status_map = {
                'timeout': 408,
                'permission_denied': 403,
                'syntax_error': 400,
                'unknown_table': 400,
                'unknown_column': 400,
                'database_error': 500,
            }
            raise HTTPException(
                status_code=status_map.get(result.error_type, 500),
                detail={'message': result.message, 'error_type': result.error_type},
            )

        # Step 6: Cache results in L2
        await cache_service.set_cached_result(sql, result)

        elapsed = (time.perf_counter() - start) * 1000
        await _save_history(
            query_id, question, sql, elapsed,
            result.row_count, was_cached, cache_level, None,
        )

        return QueryResponse(
            query_id=query_id,
            question=question,
            sql=sql,
            result=result.model_dump(),
            execution_time_ms=round(elapsed, 2),
            cached=was_cached,
            cache_level=cache_level,
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error('Query failed: %s', e, exc_info=True)
        await _save_history(
            query_id, question, sql, elapsed, None, False, None, str(e),
        )
        raise HTTPException(status_code=500, detail={'message': str(e)})
