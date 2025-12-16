from __future__ import annotations

import json
import logging
from typing import Any

# Configure structured JSON logging
logger = logging.getLogger("app.audit")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def audit(event: str, **fields: Any) -> None:
    """
    Emits a structured, machine-readable log event.
    Target: CloudWatch / Splunk / Datadog.
    """
    payload = {"event": event, **fields}
    # separators removes whitespace for compact logs
    logger.info(json.dumps(payload, separators=(",", ":"), sort_keys=True))
