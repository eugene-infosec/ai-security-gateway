from __future__ import annotations

from fastapi import HTTPException
from app.security.audit import audit
from app.security.principal import Principal

REASON_CLASSIFICATION_FORBIDDEN = "CLASSIFICATION_FORBIDDEN"


def deny(*, principal: Principal, request_id: str, path: str, reason_code: str) -> None:
    """
    Centralized deny handler.
    1. Emits forensic receipt (audit log).
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
    # This is a 'negative' invariant (what MUST NOT happen).
    if principal.role != "admin" and classification == "admin":
        deny(
            principal=principal,
            request_id=request_id,
            path=path,
            reason_code=REASON_CLASSIFICATION_FORBIDDEN,
        )
