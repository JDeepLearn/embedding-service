import logging
import json
import sys
import warnings
from datetime import datetime

from embedding_service.core.config import settings


class JsonFormatter(logging.Formatter):
    """Lightweight JSON formatter for structured, machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def configure_logging() -> None:
    """
    Configure root logging to use JSON output.
    Filters known harmless warnings for clean startup logs.
    """
    # --- Suppress specific noisy warnings ---
    warnings.filterwarnings(
        "ignore", message="Field 'model_name' in 'Settings' conflicts with protected namespace"
    )
    warnings.filterwarnings("ignore", message="`resume_download` is deprecated")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Return a structured logger for a given module name."""
    return logging.getLogger(name)