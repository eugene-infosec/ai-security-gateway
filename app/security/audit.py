from __future__ import annotations

import hashlib
import logging
from typing import Any

# Get the logger, but let the root configuration (from json_logger.py) handle the formatting
logger = logging.getLogger("app.audit")

# Removed quotes from keys because we are checking dictionary keys now, not JSON strings
FORBIDDEN_KEYS = {"body", "query", "authorization", "cookie"}
FORBIDDEN_VALUES = {"Authorization", "authorization", "Cookie", "cookie"}


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}

    # Guardrail: Check dictionary directly before logging
    # 1. Check for forbidden keys
    if any(k in FORBIDDEN_KEYS for k in payload.keys()):
        raise ValueError(
            f"unsafe_log_detected: forbidden key in {list(payload.keys())}"
        )

    # 2. Check for forbidden substrings in string values
    for v in payload.values():
        if isinstance(v, str):
            # FIX: Explicit loop to capture the specific bad word
            for bad_word in FORBIDDEN_VALUES:
                if bad_word in v:
                    raise ValueError(f"unsafe_log_detected: forbidden value {bad_word}")

    # Pass the Dict object directly.
    # The JsonFormatter will merge this into the top-level log JSON.
    logger.info(payload)
