import time
import uuid
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import PlainTextResponse
from fastapi.concurrency import run_in_threadpool
from prometheus_client import Counter, Histogram, generate_latest

from .core.config import settings
from .core.logger import get_logger, log_json
from .service import EmbeddingService
from .core.schemas import EmbeddingRequest, EmbeddingResponse, EmbeddingVector, InfoResponse


logger = get_logger("granite-embedding-service")

api_router = APIRouter()

# --------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------

REQUEST_COUNTER = Counter(
    "embedding_requests_total",
    "Total number of /embed requests.",
)
REQUEST_LATENCY = Histogram(
    "embedding_request_latency_seconds",
    "Latency of embedding requests (seconds).",
)
REQUEST_PAYLOAD_CHARS = Histogram(
    "embedding_request_payload_chars",
    "Total characters in embedding request payload.",
)
REQUEST_TEXT_LENGTH = Histogram(
    "embedding_text_length_chars",
    "Length of individual texts (characters).",
)


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def validate_inputs(texts: list[str]) -> int:
    """
    Validate counts and lengths of input texts and return total character count.

    Raises HTTPException on invalid inputs.
    """
    if not texts:
        raise HTTPException(status_code=400, detail="inputs must not be empty")

    n = len(texts)
    if n > settings.max_texts_per_request:
        raise HTTPException(
            status_code=413,
            detail=f"Too many inputs ({n}); max {settings.max_texts_per_request}",
        )

    total_chars = 0
    for i, t in enumerate(texts):
        if t is None:
            raise HTTPException(status_code=400, detail=f"Input at index {i} is null")
        length = len(t)
        if length > settings.max_chars_per_text:
            raise HTTPException(
                status_code=413,
                detail=f"Input {i} too large ({length} chars; max {settings.max_chars_per_text})",
            )
        total_chars += length

        if settings.metrics_enabled:
            REQUEST_TEXT_LENGTH.observe(length)

    if total_chars > settings.max_total_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Total payload too large ({total_chars} chars; max {settings.max_total_chars})",
        )

    if settings.metrics_enabled:
        REQUEST_PAYLOAD_CHARS.observe(total_chars)

    return total_chars


async def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    """
    Optional API key enforcement.

    If settings.api_key is set, all requests must include X-API-Key with that value.
    """
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _get_request_id(request: Request) -> str:
    """
    Retrieve request_id attached by middleware or generate one as a fallback.
    """
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = str(uuid.uuid4())
        request.state.request_id = rid
    return rid


# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------

@api_router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@api_router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    # Note: Actual metric collection is gated by settings.metrics_enabled.
    return generate_latest()


@api_router.get("/info", response_model=InfoResponse)
def info(request: Request) -> InfoResponse:
    """
    Return service and model configuration information for diagnostics.
    """
    return InfoResponse(
        model_name=settings.model_name,
        model_version=settings.model_version,
        embedding_dim=request.app.state.embedding_dim,
        device=request.app.state.device,
        service_version=request.app.version,
        max_texts_per_request=settings.max_texts_per_request,
        max_chars_per_text=settings.max_chars_per_text,
        max_total_chars=settings.max_total_chars,
        # other fields have defaults derived from settings
    )


@api_router.post("/embed", response_model=EmbeddingResponse)
async def embed(
    request: Request,
    body: EmbeddingRequest,
    _: None = Depends(verify_api_key),
) -> EmbeddingResponse:
    """
    Main embedding endpoint.

    - Validates inputs
    - Executes model.encode in a threadpool
    - Returns normalized embeddings with metadata
    """
    request_id = _get_request_id(request)

    if settings.metrics_enabled:
        REQUEST_COUNTER.inc()

    total_chars = validate_inputs(body.inputs)

    log_json(
        logger,
        "embed_start",
        request_id=request_id,
        num_inputs=len(body.inputs),
        total_chars=total_chars,
        model=body.model,
    )

    service: EmbeddingService = request.app.state.embedding_service

    start = time.time()
    try:
        embeddings = await run_in_threadpool(service.embed, body.inputs)
    except Exception as exc:  # noqa: BLE001
        log_json(
            logger,
            "embed_error",
            request_id=request_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Embedding failed") from exc

    elapsed = time.time() - start
    if settings.metrics_enabled:
        REQUEST_LATENCY.observe(elapsed)

    embedding_dim = request.app.state.embedding_dim

    # Construct EmbeddingVector list, optionally with indexes.
    embedding_vectors: list[EmbeddingVector] = []
    for idx, vec in enumerate(embeddings):
        embedding_vectors.append(
            EmbeddingVector(
                vector=vec,
                text=None,          # Can set to body.inputs[idx] if echoing text is desired
                index=idx,
            )
        )

    log_json(
        logger,
        "embed_success",
        request_id=request_id,
        num_inputs=len(embedding_vectors),
        embedding_dim=embedding_dim,
        latency_ms=int(elapsed * 1000),
    )

    response_metadata = {
        "request_id": request_id,
        "num_inputs": len(body.inputs),
        "total_chars": total_chars,
    }
    if body.metadata:
        response_metadata["request_metadata"] = body.metadata

    return EmbeddingResponse(
        model=settings.model_name,
        model_version=settings.model_version,
        embedding_dim=embedding_dim,
        embeddings=embedding_vectors,
        metadata=response_metadata,
    )