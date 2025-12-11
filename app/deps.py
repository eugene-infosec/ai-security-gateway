import logging
import os
from typing import Optional

from fastapi import Header, HTTPException, Request

from app.auth import Principal, Role

logger = logging.getLogger(__name__)

# Default to header-based identity for local dev.
# Terraform sets AUTH_MODE=jwt for the cloud deployment.
AUTH_MODE = os.getenv("AUTH_MODE", "headers").lower()


def _principal_from_headers(
    x_user: str | None,
    x_tenant: str | None,
    x_role: str | None,
) -> Principal:
    """
    Local/dev identity resolver using explicit headers.
    This is intentionally simple and fully deterministic for tests and demos.
    """
    if not (x_user and x_tenant and x_role):
        # Matches test expectation for error dictionary
        raise HTTPException(
            status_code=401,
            detail={"reason_code": "MISSING_PRINCIPAL"},
        )

    try:
        role_enum = Role(x_role.lower())
    except ValueError:
        # Matches test expectation (401 instead of 400)
        raise HTTPException(
            status_code=401,
            detail={"reason_code": "INVALID_ROLE"},
        )

    return Principal(user_id=x_user, tenant_id=x_tenant, role=role_enum)


def _principal_from_jwt(request: Request) -> Principal:
    """
    Cloud identity resolver using API Gateway HTTP API JWT authorizer claims.
    Expects claims in event['requestContext']['authorizer']['jwt']['claims']
    """
    event = request.scope.get("aws.event") or {}
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    if not claims:
        # Log only structure, never secret values
        logger.debug("No JWT claims found in aws.event; keys=%s", list(event.keys()))
        raise HTTPException(
            status_code=401,
            detail={"reason_code": "MISSING_JWT_CLAIMS"},
        )

    # Support 'sub' (OIDC standard) or 'username' (Cognito specific)
    user_id = claims.get("sub") or claims.get("username") or claims.get("cognito:username")
    tenant_id = claims.get("custom:tenant_id")
    role_claim = claims.get("custom:role")

    if not user_id or not tenant_id or not role_claim:
        raise HTTPException(
            status_code=403,
            detail={"reason_code": "INCOMPLETE_JWT_CLAIMS"},
        )

    try:
        role_enum = Role(role_claim.lower())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail={"reason_code": "INVALID_JWT_ROLE"},
        )

    return Principal(user_id=user_id, tenant_id=tenant_id, role=role_enum)


async def get_principal(
    request: Request,
    x_user: Optional[str] = Header(None, alias="X-User"),
    x_tenant: Optional[str] = Header(None, alias="X-Tenant"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
) -> Principal:
    """
    Resolve the authenticated Principal for this request.
    - In AUTH_MODE=headers (local): use X-User / X-Tenant / X-Role.
    - In AUTH_MODE=jwt (cloud): use API Gateway JWT authorizer claims.
    """
    if AUTH_MODE == "headers":
        principal = _principal_from_headers(x_user, x_tenant, x_role)
    elif AUTH_MODE == "jwt":
        principal = _principal_from_jwt(request)
    else:
        raise RuntimeError(f"Unknown AUTH_MODE={AUTH_MODE!r}")

    # Make principal visible to logging / audit middleware
    request.state.principal = principal

    return principal