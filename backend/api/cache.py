"""Cache management endpoints — stats and invalidation."""

import logging

from fastapi import APIRouter

from backend.api.schemas import CacheStatsResponse
from backend.services import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/cache', tags=['cache'])


@router.get('/stats', response_model=CacheStatsResponse)
async def cache_stats() -> CacheStatsResponse:
    """Get cache hit/miss statistics for both levels."""
    stats = await cache_service.get_cache_stats()
    return CacheStatsResponse(**stats.model_dump())


@router.post('/invalidate')
async def invalidate_cache() -> dict:
    """Clear all query caches (preserves stats)."""
    await cache_service.invalidate_all()
    return {'message': 'All caches invalidated'}
