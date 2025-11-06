from fastapi import APIRouter
from embedding_service.providers.registry import get_provider
from embedding_service.core.config import settings
from embedding_service.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


@router.get("/health", tags=["system"])
async def health_check():
    """
    Lightweight health/readiness endpoint.
    Returns service metadata and model load status.
    """
    try:
        provider = get_provider()
        model_ready = provider.ready()
        status = "ok" if model_ready else "not_ready"

        response = {
            "status": status,
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "model": provider.model(),
            "provider": provider.name(),
        }

        log.info("Health check", extra=response)
        return response

    except Exception as exc:
        log.exception("Health check failed", extra={"error": str(exc)})
        return {
            "status": "error",
            "service": settings.app_name,
            "detail": str(exc),
        }
