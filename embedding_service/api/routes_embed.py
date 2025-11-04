from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from embedding_service.providers.hf_provider import HFProvider
from embedding_service.core.config import settings
from embedding_service.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)

# Global provider instance (loads model once)
_provider = HFProvider(settings.model_name)


# ---------------------------
# Request / Response Models
# ---------------------------

class EmbedRequest(BaseModel):
    """Request schema for the /embed endpoint."""
    text: Optional[str] = Field(None, description="Single text to embed.")
    texts: Optional[List[str]] = Field(None, description="List of texts to embed.")


class SingleEmbeddingResponse(BaseModel):
    provider: str
    model: str
    dim: int
    embedding: List[float]


class BatchEmbeddingResponse(BaseModel):
    provider: str
    model: str
    count: int
    dim: int
    embeddings: List[List[float]]


# ---------------------------
# Endpoint
# ---------------------------

@router.post(
    "/embed",
    tags=["embeddings"],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"},
    },
)
async def embed(req: EmbedRequest):
    """
    Generate embeddings for one or more input texts.

    - If `text` is provided → returns one vector.
    - If `texts` is provided → returns multiple vectors.
    """
    try:
        # Single text embedding
        if req.text:
            vec = _provider.embed(req.text)
            if not vec:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Empty embedding returned",
                )
            return SingleEmbeddingResponse(
                provider=_provider.name(),
                model=_provider.model(),
                dim=len(vec),
                embedding=vec,
            )

        # Batch embedding
        if req.texts:
            vecs = _provider.embed_batch(req.texts)
            if not vecs or not vecs[0]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Empty embeddings returned",
                )
            return BatchEmbeddingResponse(
                provider=_provider.name(),
                model=_provider.model(),
                count=len(vecs),
                dim=len(vecs[0]),
                embeddings=vecs,
            )

        # Neither text nor texts provided
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'text' or 'texts' must be provided",
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Error generating embedding", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error while generating embeddings",
        ) from exc
