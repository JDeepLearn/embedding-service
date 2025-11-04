from fastapi import APIRouter
from embedding_service.core.config import settings
from embedding_service.providers.hf_provider import HFProvider
from embedding_service.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)

# Create a lightweight provider instance reference
# (We won’t re-load the model, just test readiness.)
_provider = HFProvider(settings.model_name)


@router.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint for readiness and liveness probes.
    Returns system, model, and environment information.
    """
    status_info = {
        "status": "ok" if _provider.ready() else "not_ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "model": _provider.model(),
    }
    log.info("Health check", extra=status_info)
    return status_info
