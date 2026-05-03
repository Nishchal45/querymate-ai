import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.cache import router as cache_router
from backend.api.health import router as health_router
from backend.api.history import router as history_router
from backend.api.query import router as query_router
from backend.api.schema import router as schema_router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.redis import close_redis, init_redis
from backend.core.target_database import close_target_pool, init_target_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_logging()
    logger.info('QueryMate AI starting — env=%s', settings.app_env)
    init_target_pool()
    await init_redis()
    yield
    await close_redis()
    close_target_pool()
    logger.info('QueryMate AI shutting down')


app = FastAPI(
    title='QueryMate AI',
    description='Natural language to SQL query engine',
    version='0.1.0',
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(query_router)
app.include_router(history_router)
app.include_router(schema_router)
app.include_router(cache_router)
