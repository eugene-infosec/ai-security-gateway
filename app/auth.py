from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel, Field

# 1. Define the Role Enum (Source of Truth)
class Role(str, Enum):
    admin = "admin"
    intern = "intern"

# 2. Define the Principal Model (Strict Typing)
class Principal(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=128)
    role: Role

HEADER_USER = "X-User"
HEADER_TENANT = "X-Tenant"
HEADER_ROLE = "X-Role"

def _clean(v: Optional[str]) -> Optional[str]:
    """Helper to strip whitespace and treat empty strings as None"""
    if v is None:
        return None
    v = v.strip()
    return v or None

def get_principal(request: Request) -> Principal:
    """
    Local-mode authentication:
      - Tenant + role are derived from headers (principal), not from request JSON.
      - Later, AWS mode will derive from JWT claims and ignore these headers.
    """
    user = _clean(request.headers.get(HEADER_USER))
    tenant = _clean(request.headers.get(HEADER_TENANT))
    role_raw = _clean(request.headers.get(HEADER_ROLE))

    # 401: Missing Identity
    if not user or not tenant or not role_raw:
        # We return a structured error so clients know exactly why they failed
        raise HTTPException(status_code=401, detail={"reason_code": "MISSING_PRINCIPAL"})

    role_norm = role_raw.lower()
    
    # 401: Invalid Role (e.g., "hacker" or "root")
    if role_norm not in {r.value for r in Role}:
        raise HTTPException(status_code=401, detail={"reason_code": "INVALID_ROLE"})

    principal = Principal(user_id=user, tenant_id=tenant, role=Role(role_norm))

    # Attach to request state for Audit Logging (Phase 7)
    request.state.principal = principal
    return principal