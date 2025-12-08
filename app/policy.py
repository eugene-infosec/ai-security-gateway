from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Tuple, Set

# Import directly to avoid circular dependency issues
from app.auth import Principal, Role

class Classification(str, Enum):
    public = "public"
    internal = "internal"
    admin = "admin"

def allowed_classifications(role: Role) -> Set[Classification]:
    if role == Role.admin:
        return {Classification.public, Classification.internal, Classification.admin}
    return {Classification.public, Classification.internal}

def _coerce_classification(raw: Any) -> Classification:
    # Accept already-coerced enum
    if isinstance(raw, Classification):
        return raw
    # Accept other Enums by value (generic safety)
    if isinstance(raw, Enum):
        raw = raw.value
    if raw is None:
        raise ValueError("missing classification")
    
    return Classification(str(raw).strip().lower())

def is_allowed(principal: Principal, doc: Mapping[str, Any]) -> Tuple[bool, str]:
    """
    The Core Invariant Check.
    Returns: (allowed, reason_code)
    """
    doc_tenant = doc.get("tenant_id")
    if doc_tenant != principal.tenant_id:
        return False, "TENANT_MISMATCH"

    try:
        cls = _coerce_classification(doc.get("classification"))
    except Exception:
        return False, "INVALID_CLASSIFICATION"

    if cls not in allowed_classifications(principal.role):
        return False, "CLASSIFICATION_FORBIDDEN"

    return True, "OK"