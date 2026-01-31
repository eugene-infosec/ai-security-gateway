from __future__ import annotations
import re
from typing import Any

# 1. Audit Log Allowlist (The Authority)
# Only these keys are allowed in audit payloads.
AUDIT_ALLOWED_KEYS = {
    "event",
    "schema_version",
    "request_id",
    "timestamp",
    "tenant_id",
    "user_id",
    "role",
    "status",
    "reason_code",
    "path",
    "doc_id",
    "classification",
    "results_count",
    "query_sha256",
    "query_len",
}

# 2. Validation Patterns (Exported for audit.py)
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-\._:]{1,128}$")

# 3. Sensitive Patterns (Redaction)
# Case-insensitive matches for keys, regex matches for values.
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)^(authorization|cookie|bearer|token|x-api-key|password|secret)$"
)
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\bsk_(live|test)_[0-9a-zA-Z]{10,}"),  # API Keys
    re.compile(r"\b(ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)"),  # JWTs
]


def is_sensitive_key(key: str) -> bool:
    return bool(SENSITIVE_KEY_PATTERN.search(key))


def is_sensitive_value(text: str) -> bool:
    if not text:
        return False
    # Cap scan length to prevent ReDoS
    scan_text = text[:2048]
    return any(p.search(scan_text) for p in SENSITIVE_VALUE_PATTERNS)


def scrub_recursive(obj: Any) -> Any:
    """
    Recursively scrubs sensitive data from dicts/lists/strings.
    """
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if isinstance(k, str) and is_sensitive_key(k):
                clean[k] = "[REDACTED_KEY]"
                continue
            clean[k] = scrub_recursive(v)
        return clean

    if isinstance(obj, list):
        return [scrub_recursive(i) for i in obj]

    if isinstance(obj, str):
        if is_sensitive_value(obj):
            return "[REDACTED_VALUE]"

    return obj
