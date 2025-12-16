from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_has_ok_and_request_id():
    """Prove observability plumbing works."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "request_id" in body
    assert r.headers.get("X-Request-Id") == body["request_id"]


def test_whoami_header_identity_flow():
    """Prove we can read identity headers (Critical for Phase 2)."""
    headers = {"X-User": "u1", "X-Tenant": "t1", "X-Role": "intern"}
    r = client.get("/whoami", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "u1"
    assert body["tenant_id"] == "t1"
    assert body["role"] == "intern"
    assert "request_id" in body
