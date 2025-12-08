from __future__ import annotations

import json
import logging
import sys
from typing import Any, Mapping

# Configure standard logger to output to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("app")

# THE INVARIANT: Only these keys are allowed in logs.
# Anything else raises a ValueError, preventing accidental leaks.
SAFE_KEYS = {
    "event",
    "ts",
    "request_id",
    "method",
    "path",
    "status",
    "latency_ms",
    "reason_code",
    "tenant_id",
    "role",
    "doc_ids",
    "error", # Added for exception handling
}

REDACT_KEYS = {"authorization", "cookie", "set-cookie", "body", "raw_query", "query", "headers"}

def log_safe(event: Mapping[str, Any]) -> None:
    # Enforce schema: reject unexpected keys (prevents "oops we logged body")
    unknown = set(event.keys()) - SAFE_KEYS
    if unknown:
        # This error will cause tests to fail if we try to log unsafe data
        raise ValueError(f"Unsafe log keys: {sorted(unknown)}")

    sanitized: dict[str, Any] = {}
    for k, v in event.items():
        if k.lower() in REDACT_KEYS:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v

    # distinct separators for compact JSON
    log.info(json.dumps(sanitized, separators=(",", ":"), ensure_ascii=False))