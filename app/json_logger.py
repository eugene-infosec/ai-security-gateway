import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# 1. Request correlation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

# 2. Security Configuration
FORBIDDEN_KEYS = {"body", "query", "authorization", "cookie", "x-api-key"}
FORBIDDEN_VALUES = {"Authorization", "Bearer", "sk_live_", "aws_secret_access_key"}


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

        if isinstance(record.msg, dict):
            log_record.update(record.msg)

        props = getattr(record, "props", None)
        if isinstance(props, dict):
            log_record.update(props)

        return json.dumps(log_record, default=str)


def _validate_payload_recursive(payload: Any) -> None:
    """
    Recursively scans a payload (dict, list, or primitive) for forbidden keys or values.
    Raises ValueError immediately if a violation is found.
    """
    # 1. Handle Dictionaries (Recursive)
    if isinstance(payload, dict):
        if any(k.lower() in FORBIDDEN_KEYS for k in payload.keys()):
            raise ValueError(
                f"UNSAFE_LOG: Forbidden key detected in {list(payload.keys())}"
            )
        for v in payload.values():
            _validate_payload_recursive(v)

    # 2. Handle Lists (Recursive)
    elif isinstance(payload, list):
        for item in payload:
            _validate_payload_recursive(item)

    # 3. Handle Strings (Leaf nodes)
    elif isinstance(payload, str):
        for bad in FORBIDDEN_VALUES:
            if bad in payload:
                raise ValueError(f"UNSAFE_LOG: Forbidden value '{bad}' detected.")


class SafeLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Check standard message if it's a dict or list
        if isinstance(record.msg, (dict, list)):
            _validate_payload_recursive(record.msg)

        # Check structured props (extra={"props": ...})
        if hasattr(record, "props") and isinstance(record.props, (dict, list)):
            _validate_payload_recursive(record.props)

        return True


def setup_logging(level: int = logging.INFO) -> None:
    """Configure JSON logging to stdout with Security Filter."""
    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SafeLogFilter())

    root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
