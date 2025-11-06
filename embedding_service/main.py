from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import time

from embedding_service.api import routes_embed, routes_health
from embedding_service.core import metrics
from embedding_service.core.config import settings
from embedding_service.core.logging import configure_logging, get_logger
from embedding_service.providers.registry import get_provider

configure_logging()
log = get_logger(__name__)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ------------------------------------------------------------
    # Middleware: CORS
    # ------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # configurable if needed later
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------
    # Middleware: Metrics (optional)
    # ------------------------------------------------------------
    if settings.metrics_enabled:
        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            start_time = time.perf_counter()
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            endpoint = request.url.path

            metrics.REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=getattr(response, "status_code", 500),
            ).inc()
            metrics.REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
            return response

    # ------------------------------------------------------------
    # Global Exception Handlers
    # ------------------------------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.exception("Unhandled exception", extra={"path": str(request.url), "error": str(exc)})
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": request.url.path,
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "Not Found", "path": request.url.path},
        )

    # ------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------
    app.include_router(routes_embed.router)
    app.include_router(routes_health.router)

    # Mount metrics endpoint if enabled
    if settings.metrics_enabled:
        from embedding_service.core.metrics import router as metrics_router
        app.include_router(metrics_router)

    # ------------------------------------------------------------
    # Startup Hook
    # ------------------------------------------------------------
    @app.on_event("startup")
    async def on_startup():
        try:
            provider = get_provider()  # warm up shared provider
            log.info(
                "Embedding Service started",
                extra={
                    "model": provider.model(),
                    "provider": provider.name(),
                    "env": settings.environment,
                },
            )
        except Exception as exc:
            log.exception("Startup model preload failed", extra={"error": str(exc)})

    return app


# For `uvicorn embedding_service.main:create_app --factory`
app = create_app()
