# app/core/logging.py
import sys
import logging
import structlog
from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structured logging for the entire app.
    Uses structlog for flexible output (JSON or plain text).
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format.lower() == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Returns a structured logger instance for a module.
    """
    return structlog.get_logger(name)
