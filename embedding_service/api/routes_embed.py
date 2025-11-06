from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator
from typing import List, Optional

from embedding_service.providers.registry import get_provider
from embedding_service.core.logging import get_logger
from embedding_service.core.config import settings
from embedding_service.core import metrics

log = get_logger(__name__)
router = APIRouter()

# Input limits — adjust based on hardware/throughput tradeoffs
MAX_TEXT_LEN = 4096
MAX_BATCH_SIZE = 128


class EmbedRequest(BaseModel):
    """Input schema for embedding requests."""

    text: Optional[str] = None
    texts: Optional[List[str]] = None

    @field_validator("text")
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_TEXT_LEN:
            raise ValueError(f"Single text input exceeds {MAX_TEXT_LEN} characters")
        return v

    @field_validator("texts")
    def validate_texts(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v:
            if len(v) > MAX_BATCH_SIZE:
                raise ValueError(f"Too many texts — maximum allowed is {MAX_BATCH_SIZE}")
            for t in v:
                if len(t) > MAX_TEXT_LEN:
                    raise ValueError(f"One or more texts exceed {MAX_TEXT_LEN} characters")
        return v


@router.post("/embed", tags=["embedding"])
async def embed_text(request: Request, payload: EmbedRequest):
    """
    Generate embeddings for given input text(s).
    Supports single or batch mode.
    """
    provider = get_provider()
    start_time = metrics.time_ns() if settings.metrics_enabled else 0

    try:
        if payload.text:
            embedding = provider.embed(payload.text)
            response = {
                "provider": provider.name(),
                "model": provider.model(),
                "dim": len(embedding),
                "embedding": embedding,
            }

        elif payload.texts:
            embeddings = provider.embed_batch(payload.texts)
            response = {
                "provider": provider.name(),
                "model": provider.model(),
                "count": len(embeddings),
                "dim": len(embeddings[0]) if embeddings else 0,
                "embeddings": embeddings,
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'text' or 'texts' must be provided.",
            )

        # Metrics instrumentation (only if enabled)
        if settings.metrics_enabled:
            duration = (metrics.time_ns() - start_time) / 1e9
            metrics.REQUEST_COUNT.labels(
                method="POST", endpoint="/embed", status="200"
            ).inc()
            metrics.REQUEST_LATENCY.labels(endpoint="/embed").observe(duration)

        return response

    except HTTPException:
        raise

    except ValueError as ve:
        log.warning("Validation failed", extra={"error": str(ve)})
        raise HTTPException(status_code=400, detail=str(ve)) from ve

    except Exception as exc:
        log.exception("Embedding generation failed", extra={"error": str(exc)})
        # Increment failure metric if enabled
        if settings.metrics_enabled:
            metrics.REQUEST_COUNT.labels(
                method="POST", endpoint="/embed", status="500"
            ).inc()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error while generating embeddings",
        ) from exc