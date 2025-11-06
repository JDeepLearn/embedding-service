"""
Provider registry that ensures a single embedding model instance
is created and reused across the application.

This avoids redundant SentenceTransformer loads across modules
(e.g., between /embed and /health routes).
"""

from threading import Lock
from typing import Optional

from embedding_service.providers.hf_provider import HFProvider
from embedding_service.core.config import settings
from embedding_service.core.logging import get_logger

log = get_logger(__name__)

# Internal cache + lock for thread-safe singleton
_provider_instance: Optional[HFProvider] = None
_lock = Lock()


def get_provider() -> HFProvider:
    """
    Return a singleton instance of the configured embedding provider.
    Thread-safe for concurrent FastAPI startup contexts.
    """
    global _provider_instance

    if _provider_instance is None:
        with _lock:
            if _provider_instance is None:
                try:
                    log.info("Initializing embedding provider", extra={"model_name": settings.model_name})
                    _provider_instance = HFProvider(settings.model_name)
                    log.info(
                        "Provider ready",
                        extra={
                            "provider": _provider_instance.name(),
                            "model": _provider_instance.model(),
                        },
                    )
                except Exception as exc:
                    log.exception("Failed to initialize embedding provider", extra={"error": str(exc)})
                    raise RuntimeError(f"Provider initialization failed: {exc}") from exc

    return _provider_instance