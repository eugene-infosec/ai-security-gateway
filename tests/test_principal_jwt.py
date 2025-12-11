import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app import deps
from app.auth import Role

@pytest.mark.asyncio
async def test_get_principal_from_jwt_happy_path(monkeypatch):
    # Arrange: fake API Gateway event with valid claims
    scope = {
        "type": "http",
        "aws.event": {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "user-123",
                            "custom:tenant_id": "tenant-A",
                            "custom:role": "intern",
                        }
                    }
                }
            }
        },
    }
    request = Request(scope)

    # Force JWT mode regardless of environment
    monkeypatch.setattr(deps, "AUTH_MODE", "jwt")

    # Act
    principal = await deps.get_principal(request)

    # Assert
    assert principal.user_id == "user-123"
    assert principal.tenant_id == "tenant-A"
    assert principal.role is Role.intern
    # Principal is attached to request.state for logging
    assert getattr(request.state, "principal") is principal

@pytest.mark.asyncio
async def test_get_principal_from_jwt_missing_claims(monkeypatch):
    scope = {
        "type": "http",
        "aws.event": { "requestContext": { "authorizer": { "jwt": { "claims": {} } } } }
    }
    request = Request(scope)
    monkeypatch.setattr(deps, "AUTH_MODE", "jwt")

    with pytest.raises(HTTPException) as excinfo:
        await deps.get_principal(request)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail["reason_code"] == "MISSING_JWT_CLAIMS"

@pytest.mark.asyncio
async def test_get_principal_from_jwt_invalid_role(monkeypatch):
    scope = {
        "type": "http",
        "aws.event": {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "user-123",
                            "custom:tenant_id": "tenant-A",
                            "custom:role": "root",  # Not a valid role
                        }
                    }
                }
            }
        },
    }
    request = Request(scope)
    monkeypatch.setattr(deps, "AUTH_MODE", "jwt")

    with pytest.raises(HTTPException) as excinfo:
        await deps.get_principal(request)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["reason_code"] == "INVALID_JWT_ROLE"