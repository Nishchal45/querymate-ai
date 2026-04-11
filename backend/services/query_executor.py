"""Query Executor — safely runs validated SQL against the target database
with timeout enforcement, row limits, and structured error handling.
"""

import logging
import time
from typing import Any, Optional

import psycopg2
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.target_database import get_target_connection

logger = logging.getLogger(__name__)


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class QueryError(BaseModel):
    error_type: str
    message: str


def execute_query(sql: str) -> QueryResult | QueryError:
    """Execute validated SQL against the target database.

    Safety mechanisms:
        - statement_timeout: set at connection level (via target_database.py)
        - max_result_rows: limits fetched rows to prevent memory exhaustion
        - read-only connection: enforced at psycopg2 and DB role levels

    Args:
        sql: Validated SQL string (must have passed sql_validator first)

    Returns:
        QueryResult on success, QueryError on failure
    """
    start = time.perf_counter()

    try:
        with get_target_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)

                # Get column names from cursor description
                columns = [desc[0] for desc in cur.description or []]

                # Fetch with row limit
                max_rows = settings.max_result_rows
                rows_raw = cur.fetchmany(max_rows + 1)

                truncated = len(rows_raw) > max_rows
                if truncated:
                    rows_raw = rows_raw[:max_rows]

                # Convert to serializable lists
                rows = [list(row) for row in rows_raw]

                elapsed_ms = (time.perf_counter() - start) * 1000

                logger.info(
                    'Query executed — %d rows in %.1fms%s',
                    len(rows),
                    elapsed_ms,
                    ' (truncated)' if truncated else '',
                )

                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=round(elapsed_ms, 2),
                    truncated=truncated,
                )

    except psycopg2.extensions.QueryCanceledError:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning('Query timed out after %.1fms', elapsed_ms)
        return QueryError(
            error_type='timeout',
            message=f'Query took too long and was cancelled '
                    f'(limit: {settings.query_timeout_seconds}s). '
                    f'Try a more specific question.',
        )

    except psycopg2.errors.InsufficientPrivilege:
        logger.error('Permission denied — this should not happen after validation')
        return QueryError(
            error_type='permission_denied',
            message='Query requires permissions that are not available. '
                    'Only SELECT queries on user tables are allowed.',
        )

    except psycopg2.errors.SyntaxError as e:
        logger.warning('SQL syntax error: %s', e.pgerror)
        return QueryError(
            error_type='syntax_error',
            message='The generated SQL has a syntax error. '
                    'Try rephrasing your question.',
        )

    except psycopg2.errors.UndefinedTable as e:
        logger.warning('Unknown table: %s', e.pgerror)
        return QueryError(
            error_type='unknown_table',
            message='The query references a table that does not exist. '
                    'Check the schema explorer for available tables.',
        )

    except psycopg2.errors.UndefinedColumn as e:
        logger.warning('Unknown column: %s', e.pgerror)
        return QueryError(
            error_type='unknown_column',
            message='The query references a column that does not exist. '
                    'Try rephrasing your question.',
        )

    except psycopg2.Error as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error('Database error: %s', e.pgerror or str(e))
        return QueryError(
            error_type='database_error',
            message='An unexpected database error occurred. '
                    'Please try again or rephrase your question.',
        )
