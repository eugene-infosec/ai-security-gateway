from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    role: str


def resolve_principal_from_headers(headers) -> Principal:
    return Principal(
        user_id=headers.get("X-User", "anonymous"),
        tenant_id=headers.get("X-Tenant", "unknown"),
        role=headers.get("X-Role", "unknown"),
    )


def resolve_principal_from_jwt_claims(claims: dict[str, Any]) -> Principal:
    """
    We rely on Cognito IdToken claims:
      - sub
      - custom:tenant_id
      - custom:role
    """
    user_id = str(claims.get("sub", "")).strip()
    tenant_id = str(claims.get("custom:tenant_id", "")).strip()
    role = str(claims.get("custom:role", "")).strip()

    if not user_id or not tenant_id or not role:
        raise ValueError(
            "Missing required JWT claims (sub/custom:tenant_id/custom:role)"
        )

    return Principal(user_id=user_id, tenant_id=tenant_id, role=role)
