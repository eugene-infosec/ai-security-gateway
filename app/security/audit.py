from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger("app.audit")
# Ensure we don't duplicate handlers if reloaded
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

FORBIDDEN_SUBSTRINGS = (
    '"body"',
    '"query"',
    "Authorization",
    "authorization",
    "Cookie",
    "cookie",
)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    line = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # Guardrail: we never emit forbidden keys/strings into logs.
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in line:
            # In a real app we might redact, here we raise to fail the gate
            raise ValueError(f"unsafe_log_detected: {bad}")

    logger.info(line)
