from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    role: str  # "intern" | "admin"


def resolve_principal_from_headers(headers) -> Principal:
    """
    Dev/Local Mode: Trust the headers explicitly.
    In Prod/AWS: This will be replaced by JWT claim mapping.
    """
    return Principal(
        user_id=headers.get("X-User", "anonymous"),
        tenant_id=headers.get("X-Tenant", "unknown"),
        role=headers.get("X-Role", "unknown"),
    )
