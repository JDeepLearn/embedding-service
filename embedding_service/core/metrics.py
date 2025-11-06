# embedding_service/core/metrics.py
"""
Prometheus metrics integration for the Embedding Service.

This module defines counters and histograms that are safe to import
across modules and conditionally mounted if metrics are enabled.
"""

import time
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
from fastapi import APIRouter, Response

from embedding_service.core.config import settings

# ------------------------------------------------------------
# Metric definitions
# ------------------------------------------------------------
REQUEST_COUNT = Counter(
    "embedding_service_requests_total",
    "Total HTTP requests handled by the embedding service",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "embedding_service_request_latency_seconds",
    "Latency of HTTP requests by endpoint (seconds)",
    ["endpoint"],
)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def time_ns() -> int:
    """Return current time in nanoseconds (for fine-grained latency tracking)."""
    return time.perf_counter_ns()


# ------------------------------------------------------------
# FastAPI route for /metrics
# ------------------------------------------------------------
router = APIRouter()


@router.get("/metrics", tags=["system"])
async def metrics_endpoint() -> Response:
    """
    Prometheus-compatible metrics endpoint.
    Exposed only if METRICS_ENABLED=true.
    """
    if not settings.metrics_enabled:
        return Response(status_code=404, content="Metrics disabled")

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)