import pytest
from app.security.principal import resolve_principal_from_jwt_claims


def test_resolve_principal_from_jwt_claims_happy_path():
    claims = {
        "sub": "user-123",
        "custom:tenant_id": "tenant-a",
        "custom:role": "intern",
    }
    p = resolve_principal_from_jwt_claims(claims)
    assert p.user_id == "user-123"
    assert p.tenant_id == "tenant-a"
    assert p.role == "intern"


def test_resolve_principal_from_jwt_claims_missing_fields():
    with pytest.raises(ValueError):
        resolve_principal_from_jwt_claims({"sub": "x"})
