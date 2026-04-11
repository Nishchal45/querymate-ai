import logging
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2 import pool

from backend.core.config import settings

logger = logging.getLogger(__name__)

_pool: pool.ThreadedConnectionPool | None = None


def _parse_dsn() -> dict:
    """Parse the target database URL into psycopg2 connection params."""
    parsed = urlparse(settings.target_database_url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'dbname': parsed.path.lstrip('/'),
        'user': parsed.username or 'demo_user',
        'password': parsed.password or 'demo_secret',
    }


def init_target_pool() -> None:
    """Create the connection pool for the target database."""
    global _pool
    if _pool is not None:
        return

    params = _parse_dsn()
    _pool = pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        **params,
    )
    logger.info(
        'Target DB pool created — host=%s dbname=%s user=%s',
        params['host'],
        params['dbname'],
        params['user'],
    )


def close_target_pool() -> None:
    """Close all connections in the pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info('Target DB pool closed')


@contextmanager
def get_target_connection():
    """Yield a read-only connection with statement timeout.

    Safety layers applied at connection level:
    - statement_timeout: cancels queries exceeding the limit
    - default_transaction_read_only: enforces read-only at connection level
    """
    if _pool is None:
        init_target_pool()

    conn = _pool.getconn()
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(
                'SET statement_timeout = %s',
                (f'{settings.query_timeout_seconds}s',),
            )
        yield conn
    finally:
        _pool.putconn(conn)
