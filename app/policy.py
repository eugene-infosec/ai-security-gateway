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
    """
    Returns the set of data labels a role is allowed to see.
    """
    if role == Role.admin:
        return {Classification.public, Classification.internal, Classification.admin}
    return {Classification.public, Classification.internal}

def is_allowed(principal: Principal, doc: Mapping[str, Any]) -> Tuple[bool, str]:
    """
    The Core Invariant Check.
    Determines if a Principal can access a specific Document.
    
    Returns:
      (allowed, reason_code)
    """
    # 1. Tenant Isolation (The most critical check)
    doc_tenant = doc.get("tenant_id")
    if doc_tenant != principal.tenant_id:
        return False, "TENANT_MISMATCH"

    # 2. Classification Check
    raw_cls = doc.get("classification")
    try:
        # robustly handle missing or string-based enums
        cls = Classification(str(raw_cls))
    except Exception:
        return False, "INVALID_CLASSIFICATION"

    if cls not in allowed_classifications(principal.role):
        return False, "CLASSIFICATION_FORBIDDEN"

    return True, "OK"