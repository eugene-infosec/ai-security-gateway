from __future__ import annotations

from typing import Dict, Set
from fastapi import HTTPException
from app.security.audit import audit
from app.security.principal import Principal

REASON_CLASSIFICATION_FORBIDDEN = "CLASSIFICATION_FORBIDDEN"
REASON_ROLE_UNKNOWN = "ROLE_UNKNOWN_FAIL_CLOSED"

# Explicit Policy Definition (Data-Driven)
ROLE_POLICY: Dict[str, Set[str]] = {
    "intern": {"public"},
    "staff": {"public"},
    "admin": {"public", "admin"},
}


def get_allowed_classifications(role: str) -> Set[str]:
    """
    Returns the set of allowed classifications for a given role.
    Fails closed (returns empty set) if role is unknown.
    """
    return ROLE_POLICY.get(role, set())


def deny(*, principal: Principal, request_id: str, path: str, reason_code: str) -> None:
    """
    Centralized deny handler.
    1. Emits audit-grade deny receipt.
    2. Raises 403 exception.
    """
    audit(
        "access_denied",
        reason_code=reason_code,
        tenant_id=principal.tenant_id,
        role=principal.role,
        user_id=principal.user_id,
        status=403,
        path=path,
        request_id=request_id,
    )
    raise HTTPException(
        status_code=403, detail={"reason_code": reason_code, "request_id": request_id}
    )


def authorize_ingest(
    *, principal: Principal, classification: str, request_id: str, path: str
) -> None:
    # Phase 3 Rule: Interns (non-admins) may never ingest admin-classified docs.
    if principal.role != "admin" and classification == "admin":
        deny(
            principal=principal,
            request_id=request_id,
            path=path,
            reason_code=REASON_CLASSIFICATION_FORBIDDEN,
        )
