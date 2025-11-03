from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api import routes_embed, routes_health
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.observability import ObservabilityMiddleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Embedding Service",
        version=settings.app_version,
        description="FastAPI microservice for local and on-prem embedding generation",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Observability
    app.add_middleware(ObservabilityMiddleware)

    # Routers
    app.include_router(routes_health.router)
    app.include_router(routes_embed.router)

    # Expose Prometheus metrics at /metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app
