from fastapi.testclient import TestClient
from app.main import app
from app.auth import Principal, Role
from app.policy import is_allowed

client = TestClient(app)

# --- PART 1: AUTH ---

def test_whoami_requires_principal():
    r = client.get("/whoami")
    assert r.status_code == 401
    assert r.json()["detail"]["reason_code"] == "MISSING_PRINCIPAL"

def test_whoami_rejects_invalid_role():
    r = client.get(
        "/whoami",
        headers={"X-User": "u1", "X-Tenant": "t1", "X-Role": "root"},
    )
    assert r.status_code == 401
    assert r.json()["detail"]["reason_code"] == "INVALID_ROLE"

def test_whoami_returns_normalized_principal():
    # Helper: Send "INTERN" (uppercase), expect "intern" (lowercase)
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
    # Intern A tries to access Doc B -> DENY
    allowed, reason = is_allowed(p, {"tenant_id": "B", "classification": "public"})
    assert allowed is False
    assert reason == "TENANT_MISMATCH"

def test_policy_intern_cannot_access_admin():
    p = Principal(user_id="u", tenant_id="A", role=Role.intern)
    # Intern A tries to access Admin Doc A -> DENY
    allowed, reason = is_allowed(p, {"tenant_id": "A", "classification": "admin"})
    assert allowed is False
    assert reason == "CLASSIFICATION_FORBIDDEN"

def test_policy_admin_can_access_admin():
    p = Principal(user_id="u", tenant_id="A", role=Role.admin)
    # Admin A tries to access Admin Doc A -> ALLOW
    allowed, reason = is_allowed(p, {"tenant_id": "A", "classification": "admin"})
    assert allowed is True
    assert reason == "OK"