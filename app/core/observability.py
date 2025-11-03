import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from prometheus_client import Counter, Histogram
from app.core.logging import get_logger

log = get_logger("observability")

# Prometheus metrics
REQ_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "path", "status_code"],
)

REQ_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks request count and latency
    for Prometheus metrics and logs request duration.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        status_code = 500  # Default in case of exception
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 200)
        except Exception as e:
            log.error("Unhandled request error", error=str(e))
            # Return safe 500 response (optional for resilience)
            response = JSONResponse(
                {"error": "Internal Server Error", "detail": str(e)},
                status_code=500,
            )
            status_code = 500
        finally:
            duration = time.time() - start_time
            REQ_COUNTER.labels(request.method, request.url.path, status_code).inc()
            REQ_LATENCY.labels(request.method, request.url.path).observe(duration)
            log.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
            )

        return response
