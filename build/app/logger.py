from __future__ import annotations

import json
import logging
import sys
from typing import Any, Mapping, List

# Configure standard logger to output to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("app")

SAFE_KEYS = {
    "event", "ts", "request_id", "method", "path", "status", "latency_ms",
    "reason_code", "tenant_id", "role", "doc_ids", "error", "classification",
    "match_count", "user"
}

REDACT_KEYS = {"authorization", "cookie", "set-cookie", "body", "raw_query", "query", "headers"}

# NEW: In-Memory Sink for Testing
# This allows our tests to "read" the logs and verify no secrets leaked.
_TEST_SINK: List[dict] = []

def get_sink() -> List[dict]:
    return _TEST_SINK

def clear_sink():
    _TEST_SINK.clear()

def log_safe(event: Mapping[str, Any]) -> None:
    # 1. Enforce Schema
    unknown = set(event.keys()) - SAFE_KEYS
    if unknown:
        raise ValueError(f"Unsafe log keys: {sorted(unknown)}")

    # 2. Redact & Sanitize
    sanitized: dict[str, Any] = {}
    for k, v in event.items():
        if k.lower() in REDACT_KEYS:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v

    # 3. Emit to Stdout (Production)
    log.info(json.dumps(sanitized, separators=(",", ":"), ensure_ascii=False))
    
    # 4. Emit to Sink (Testing)
    # We store the *sanitized* version to prove redaction worked.
    _TEST_SINK.append(sanitized)