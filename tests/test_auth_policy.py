from fastapi.testclient import TestClient
from app.main import app
from app.auth import Principal, Role
from app.policy import is_allowed

client = TestClient(app)

# --- PART 1: AUTH ---

def test_whoami_requires_principal():
    r = client.get("/whoami")
    assert r.status_code == 401
    # FIX: Check top-level "reason_code", not "detail.reason_code"
    assert r.json()["reason_code"] == "MISSING_PRINCIPAL"

def test_whoami_rejects_invalid_role():
    r = client.get(
        "/whoami",
        headers={"X-User": "u1", "X-Tenant": "t1", "X-Role": "root"},
    )
    assert r.status_code == 401
    assert r.json()["reason_code"] == "INVALID_ROLE"

def test_whoami_returns_normalized_principal():
    r = client.get(
        "/whoami",
        headers={"X-User": "u1", "X-Tenant": "t1", "X-Role": "INTERN"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "u1"
    assert body["tenant_id"] == "t1"
    assert body["role"] == "intern"

# --- PART 2: POLICY ---

def test_policy_tenant_mismatch():
    p = Principal(user_id="u", tenant_id="A", role=Role.intern)
    allowed, reason = is_allowed(p, {"tenant_id": "B", "classification": "public"})
    assert allowed is False
    assert reason == "TENANT_MISMATCH"

def test_policy_intern_cannot_access_admin():
    p = Principal(user_id="u", tenant_id="A", role=Role.intern)
    allowed, reason = is_allowed(p, {"tenant_id": "A", "classification": "admin"})
    assert allowed is False
    assert reason == "CLASSIFICATION_FORBIDDEN"

def test_policy_admin_can_access_admin():
    p = Principal(user_id="u", tenant_id="A", role=Role.admin)
    allowed, reason = is_allowed(p, {"tenant_id": "A", "classification": "admin"})
    assert allowed is True
    assert reason == "OK"