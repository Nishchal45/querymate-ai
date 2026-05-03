"""Redis connection management for async operations."""

import logging

import redis.asyncio as aioredis

from backend.core.config import settings

logger = logging.getLogger(__name__)

_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """Create the Redis connection pool."""
    global _pool
    if _pool is not None:
        return

    _pool = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
    )
    # Verify connectivity
    await _pool.ping()
    logger.info('Redis connected — %s', settings.redis_url)


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info('Redis connection closed')


def get_redis() -> aioredis.Redis:
    """Get the Redis client. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError('Redis not initialized — call init_redis() first')
    return _pool
