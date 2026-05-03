"""Cache Service — two-level Redis caching for NL2SQL queries.

Level 1 (NL → SQL):
  - Caches the LLM's SQL output keyed by normalized question
  - Same question asked twice → skip LLM entirely (~1.5s saved)
  - TTL: 1 hour (query intent doesn't change frequently)

Level 2 (SQL → Results):
  - Caches query results keyed by SQL hash
  - Different questions producing same SQL → skip DB execution (~100ms saved)
  - TTL: 5 minutes (underlying data changes more frequently)

Performance impact:
  Cold query:     ~1.8s  (LLM + DB)
  L1 hit only:    ~0.15s (skip LLM, still hit DB)
  L1 + L2 hit:    <5ms   (Redis only)
"""

import hashlib
import json
import logging
import re

from pydantic import BaseModel

from backend.core.config import settings
from backend.core.redis import get_redis
from backend.services.query_executor import QueryResult

logger = logging.getLogger(__name__)

# Redis key prefixes
_NL_PREFIX = 'querymate:nl:'
_SQL_PREFIX = 'querymate:sql:'
_STATS_PREFIX = 'querymate:stats:'


class CacheStats(BaseModel):
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l1_hit_rate: float = 0.0
    l2_hit_rate: float = 0.0


def _normalize_query(nl_query: str) -> str:
    """Normalize a natural language query for cache key consistency.

    'How many orders?' and 'how many orders' should hit the same cache entry.
    """
    text = nl_query.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)      # Collapse whitespace
    return text


def _hash_key(value: str) -> str:
    """SHA-256 hash for cache keys."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# ── L1 Cache: Natural Language → SQL ──

async def get_cached_sql(nl_query: str) -> str | None:
    """Check L1 cache for a previously generated SQL query."""
    r = get_redis()
    key = _NL_PREFIX + _hash_key(_normalize_query(nl_query))

    result = await r.get(key)
    if result is not None:
        await r.incr(_STATS_PREFIX + 'l1_hits')
        logger.debug('L1 cache HIT — %s', nl_query[:50])
        return result

    await r.incr(_STATS_PREFIX + 'l1_misses')
    logger.debug('L1 cache MISS — %s', nl_query[:50])
    return None


async def set_cached_sql(nl_query: str, sql: str) -> None:
    """Store a NL→SQL mapping in L1 cache."""
    r = get_redis()
    key = _NL_PREFIX + _hash_key(_normalize_query(nl_query))
    await r.set(key, sql, ex=settings.cache_ttl_nl_sql)


# ── L2 Cache: SQL → Results ──

async def get_cached_result(sql: str) -> QueryResult | None:
    """Check L2 cache for previously computed query results."""
    r = get_redis()
    key = _SQL_PREFIX + _hash_key(sql)

    result = await r.get(key)
    if result is not None:
        await r.incr(_STATS_PREFIX + 'l2_hits')
        logger.debug('L2 cache HIT')
        return QueryResult(**json.loads(result))

    await r.incr(_STATS_PREFIX + 'l2_misses')
    logger.debug('L2 cache MISS')
    return None


async def set_cached_result(sql: str, result: QueryResult) -> None:
    """Store SQL→Results mapping in L2 cache."""
    r = get_redis()
    key = _SQL_PREFIX + _hash_key(sql)
    await r.set(key, result.model_dump_json(), ex=settings.cache_ttl_sql_results)


# ── Cache Management ──

async def invalidate_all() -> None:
    """Clear all query caches (preserves stats)."""
    r = get_redis()
    async for key in r.scan_iter(f'{_NL_PREFIX}*'):
        await r.delete(key)
    async for key in r.scan_iter(f'{_SQL_PREFIX}*'):
        await r.delete(key)
    logger.info('All query caches invalidated')


async def get_cache_stats() -> CacheStats:
    """Get cache hit/miss statistics."""
    r = get_redis()
    l1_hits = int(await r.get(_STATS_PREFIX + 'l1_hits') or 0)
    l1_misses = int(await r.get(_STATS_PREFIX + 'l1_misses') or 0)
    l2_hits = int(await r.get(_STATS_PREFIX + 'l2_hits') or 0)
    l2_misses = int(await r.get(_STATS_PREFIX + 'l2_misses') or 0)

    l1_total = l1_hits + l1_misses
    l2_total = l2_hits + l2_misses

    return CacheStats(
        l1_hits=l1_hits,
        l1_misses=l1_misses,
        l2_hits=l2_hits,
        l2_misses=l2_misses,
        l1_hit_rate=round(l1_hits / l1_total, 3) if l1_total > 0 else 0.0,
        l2_hit_rate=round(l2_hits / l2_total, 3) if l2_total > 0 else 0.0,
    )
