# embedding-service/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status
import time

from embedding_service.core.config import settings
from embedding_service.core.logging import configure_logging, get_logger
from embedding_service.core import metrics
from embedding_service.api import routes_embed, routes_health

log = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Application factory for the Embedding Service.

    Initializes logging, metrics, exception handling, and routes.
    Keeps the app stateless, testable, and production-grade.
    """
    # --- Logging ---
    configure_logging()

    # --- Application ---
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.environment != "prod" else None,
        redoc_url=None,
    )

    # --- Middleware for Metrics ---
    @app.middleware("http")
    async def add_metrics(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        metrics.REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        metrics.REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        return response

    # --- Routers ---
    app.include_router(routes_health.router)
    app.include_router(routes_embed.router)
    app.include_router(metrics.router)

    # --- Global Exception Handlers ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "path": str(request.url.path)},
        )

    log.info(f"{settings.app_name} initialized", extra={"env": settings.environment})
    return app


# For Uvicorn compatibility without --factory flag
app = create_app()