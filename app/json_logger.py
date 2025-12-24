import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Request correlation across async call chains.
# Middleware sets this per request; formatter injects it into every log line.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", None) or request_id_ctx.get()

        log_record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": rid,
            "message": record.getMessage(),
        }

        # If the message is a dict (common for structured events), merge it.
        if isinstance(record.msg, dict):
            log_record.update(record.msg)

        # If caller provided additional structured fields via `extra={"props": {...}}`.
        props = getattr(record, "props", None)
        if isinstance(props, dict):
            log_record.update(props)

        return json.dumps(log_record, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure JSON logging to stdout."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any pre-existing handlers to avoid duplicate logs.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Keep uvicorn loggers consistent with the root formatter.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True


def get_logger(name: str = "ai-security-gateway") -> logging.Logger:
    return logging.getLogger(name)
