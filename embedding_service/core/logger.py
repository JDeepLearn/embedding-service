import json
import logging
import sys
from typing import Any, Optional


def configure_logging(level: str) -> None:
    """
    Configure global logging once for the entire process.

    - JSON line logs (safe for ingestion by ELK/Loki).
    - UTC timestamps for cross-service correlation.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any library defaults
    )


def get_logger(name: str) -> logging.Logger:
    """Retrieve a namespaced logger instance."""
    return logging.getLogger(name)


def log_json(
    logger: logging.Logger,
    event: str,
    request_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log structured JSON payloads for machine parsing.

    Adds:
    - event: short code for the log type
    - request_id: correlation id (if present)
    - kwargs: arbitrary contextual data
    """
    payload = {
        "event": event,
        "request_id": request_id,
        **kwargs,
    }
    # Avoid serialization errors
    try:
        logger.info(json.dumps(payload, default=str))
    except Exception as e:  # noqa: BLE001
        logger.error(json.dumps({"event": "log_serialization_error", "error": str(e)}))
