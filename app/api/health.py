from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])

START_TIME = datetime.now(timezone.utc)


@router.get("/health")
async def health():
    """
    Overall application health.
    """
    return {
        "status": "healthy",
        "application": settings.app_name,
        "environment": settings.environment,
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live")
async def live():
    """
    Liveness probe.
    """
    return {
        "status": "alive",
    }


@router.get("/ready")
async def ready():
    """
    Readiness probe.
    """
    return {
        "status": "ready",
    }
