from __future__ import annotations
from typing import Any


def get_jwt_claims_from_asgi_scope(scope: dict[str, Any]) -> dict[str, Any] | None:
    """
    Mangum injects the raw AWS event into request.scope["aws.event"].
    For API Gateway HTTP API (v2), JWT authorizer claims live at:
      event.requestContext.authorizer.jwt.claims
    """
    event = scope.get("aws.event")
    if not isinstance(event, dict):
        return None

    rc = event.get("requestContext")
    if not isinstance(rc, dict):
        return None

    authorizer = rc.get("authorizer")
    if not isinstance(authorizer, dict):
        return None

    jwt = authorizer.get("jwt")
    if not isinstance(jwt, dict):
        return None

    return jwt.get("claims")
