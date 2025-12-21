import logging
import json
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
        }

        # NEW: If the message is a dict (from audit), merge it into the top level
        if isinstance(record.msg, dict):
            log_record.update(record.msg)
        else:
            log_record["message"] = record.getMessage()

        # Add request_id if available in extra
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        return json.dumps(log_record)


def setup_logging():
    """Call this once in your main.py startup"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(handler)
