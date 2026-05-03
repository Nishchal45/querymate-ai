from fastapi import APIRouter

router = APIRouter(tags=['health'])


@router.get('/health')
async def health() -> dict:
    """Basic liveness check."""
    return {'status': 'healthy', 'version': '0.1.0'}


@router.get('/health/ready')
async def readiness() -> dict:
    """Readiness check — verifies DB and Redis are reachable.
    Full implementation added when database and Redis modules are built.
    """
    return {
        'status': 'ready',
        'services': {
            'app_db': 'not_configured',
            'target_db': 'not_configured',
            'redis': 'not_configured',
        },
    }
