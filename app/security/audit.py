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


def _validate_payload(payload: Any) -> None:
    """
    Recursively scans a payload (dict, list, or primitive) for forbidden keys or values.
    Raises ValueError immediately if a violation is found.
    """
    # 1. Handle Dictionaries (Recursive)
    if isinstance(payload, dict):
        # Key Check (Shallow for this level)
        if any(k in FORBIDDEN_KEYS for k in payload.keys()):
            raise ValueError(
                f"unsafe_log_detected: forbidden key in {list(payload.keys())}"
            )
        # Value Check (Recursive)
        for v in payload.values():
            _validate_payload(v)

    # 2. Handle Lists (Recursive)
    elif isinstance(payload, list):
        for item in payload:
            _validate_payload(item)

    # 3. Handle Strings (Leaf nodes)
    elif isinstance(payload, str):
        for bad_word in FORBIDDEN_VALUES:
            if bad_word in payload:
                raise ValueError(f"unsafe_log_detected: forbidden value '{bad_word}'")


def audit(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}

    # Guardrail: Deep recursive check before logging
    # This prevents secrets from hiding in nested JSON (e.g., metadata={"api_key": "..."})
    _validate_payload(payload)

    # The JsonFormatter will merge this into the top-level log JSON.
    logger.info(payload)
