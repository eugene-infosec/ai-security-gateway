import os
from fastapi import Request, HTTPException
from app.auth import Principal, Role

def get_principal(request: Request) -> Principal:
    # SECURITY NOTE:
    # The AWS deployment runs in header-auth demo mode for easy verification.
    # In production, identity would be derived from JWT/authorizer claims.
    
    user = (request.headers.get("X-User") or "").strip()
    tenant = (request.headers.get("X-Tenant") or "").strip()
    role_raw = (request.headers.get("X-Role") or "").strip().lower()

    if not user or not tenant or not role_raw:
        raise HTTPException(401, detail={"reason_code": "MISSING_PRINCIPAL"})
    
    try:
        role = Role(role_raw)
    except ValueError:
        raise HTTPException(401, detail={"reason_code": "INVALID_ROLE"})

    principal = Principal(user_id=user, tenant_id=tenant, role=role)
    request.state.principal = principal
    return principal