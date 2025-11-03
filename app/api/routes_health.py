from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="Health check", tags=["system"])
async def health_check():
    """
    Simple readiness & liveness probe.
    Used by Docker, Kubernetes, and monitoring systems.
    """
    return {"status": "ok", "version": settings.app_version}
