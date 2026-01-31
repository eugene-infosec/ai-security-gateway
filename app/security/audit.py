from __future__ import annotations
import hashlib
import logging
from typing import Any, Dict
from app.security.log_safety import AUDIT_ALLOWED_KEYS, SAFE_ID_PATTERN

logger = logging.getLogger("app.audit")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_value(key: str, value: Any) -> Any:
    """Ensures values are safe primitives."""
    if value is None:
        return None

    if isinstance(value, int):
        return value

    s_val = str(value).strip()

    # Strict ID validation using the Shared Pattern
    if key.endswith("_id") or key == "role" or key == "event":
        if not SAFE_ID_PATTERN.match(s_val):
            return "invalid_format"

    if len(s_val) > 512:
        return s_val[:512] + "...(truncated)"

    return s_val


def audit(event: str, **fields: Any) -> None:
    """
    Emits a structured audit log using a strict allowlist schema.
    NEVER raises exceptions.
    """
    try:
        payload: Dict[str, Any] = {"event": event, "schema_version": "1.0"}

        # Use the Unified Allowlist
        for k, v in fields.items():
            if k in AUDIT_ALLOWED_KEYS:
                safe_v = _sanitize_value(k, v)
                if safe_v is not None:
                    payload[k] = safe_v

        logger.info("audit_event", extra={"props": payload})

    except Exception:
        # Never crash the request
        logger.error(
            "audit_system_failure",
            extra={"props": {"event": "audit_system_failure", "schema_version": "1.0"}},
        )
