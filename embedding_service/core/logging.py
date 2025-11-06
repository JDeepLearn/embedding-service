import logging
import json
import sys
from datetime import datetime

from embedding_service.core.config import settings


# Keys that are part of the standard LogRecord and should not be duplicated
_BASE_LOG_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class JsonFormatter(logging.Formatter):
    """JSON formatter that preserves both message and extra structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        # Base envelope
        log_record: dict = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add any non-standard attributes (set via `extra={...}`)
        for key, value in record.__dict__.items():
            if key not in _BASE_LOG_FIELDS and key not in ("message", "asctime"):
                log_record[key] = value

        # Exception info, if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def configure_logging() -> None:
    """
    Configure root logging to use JSON output.
    Filters known harmless warnings for clean startup logs.
    """

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Return a structured logger for a given module name."""
    return logging.getLogger(name)