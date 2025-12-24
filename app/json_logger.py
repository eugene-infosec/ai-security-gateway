import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# 1. Request correlation (Restored)
# Middleware sets this per request; formatter injects it into every log line.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

# 2. Security Configuration
FORBIDDEN_KEYS = {"body", "query", "authorization", "cookie", "x-api-key"}
FORBIDDEN_VALUES = {"Authorization", "Bearer", "sk_live_", "aws_secret_access_key"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Restore request_id logic
        rid = getattr(record, "request_id", None) or request_id_ctx.get()

        log_record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": rid,
            "message": record.getMessage(),
        }

        # Merge dict messages (structured logs)
        if isinstance(record.msg, dict):
            log_record.update(record.msg)

        # Merge extra props
        props = getattr(record, "props", None)
        if isinstance(props, dict):
            log_record.update(props)

        return json.dumps(log_record, default=str)


class SafeLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Check standard message if it's a dict
        if isinstance(record.msg, dict):
            self._validate(record.msg)

        # Check structured props (extra={"props": ...})
        if hasattr(record, "props") and isinstance(record.props, dict):
            self._validate(record.props)

        return True

    def _validate(self, payload: dict):
        # Key Scan
        if any(k.lower() in FORBIDDEN_KEYS for k in payload.keys()):
            raise ValueError(
                f"UNSAFE_LOG: Forbidden key detected in {list(payload.keys())}"
            )

        # Value Scan
        for v in payload.values():
            if isinstance(v, str):
                for bad in FORBIDDEN_VALUES:
                    if bad in v:
                        raise ValueError(
                            f"UNSAFE_LOG: Forbidden value '{bad}' detected."
                        )


def setup_logging(level: int = logging.INFO) -> None:
    """Configure JSON logging to stdout with Security Filter."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Apply the Security Filter Globally
    handler.addFilter(SafeLogFilter())

    root.addHandler(handler)

    # Keep uvicorn loggers clean (Restored)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
