from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()


# ---------------------------
# Metric Definitions
# ---------------------------

REQUEST_COUNT = Counter(
    "embedding_service_requests_total",
    "Total number of HTTP requests handled by the embedding service",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "embedding_service_request_latency_seconds",
    "Request latency in seconds by endpoint",
    ["endpoint"],
)


# ---------------------------
# Endpoint
# ---------------------------

@router.get("/metrics", tags=["system"])
async def metrics() -> Response:
    """
    Exposes Prometheus-compatible metrics for scraping.
    Returns cumulative counters and histograms for monitoring systems.
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
