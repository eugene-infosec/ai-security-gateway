import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from app.security.log_safety import scrub_recursive, is_sensitive_value

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

        if isinstance(record.msg, dict):
            log_record.update(record.msg)

        props = getattr(record, "props", None)
        if isinstance(props, dict):
            log_record.update(props)

        return json.dumps(log_record, default=str)


class SafeLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitizes the log record in-place using shared logic.
        NEVER raises an exception.
        """
        try:
            # 1. Check raw message string
            if isinstance(record.msg, str) and is_sensitive_value(record.msg):
                record.msg = "[REDACTED_MSG_STRING]"

            # 2. Scrub dictionary message
            if isinstance(record.msg, dict):
                record.msg = scrub_recursive(record.msg)

            # 3. Scrub extra props
            if hasattr(record, "props") and isinstance(record.props, dict):
                record.props = scrub_recursive(record.props)

        except Exception:
            record.msg = "log_scrubbing_error"
            if hasattr(record, "props"):
                record.props = {}

        return True


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SafeLogFilter())
    root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
