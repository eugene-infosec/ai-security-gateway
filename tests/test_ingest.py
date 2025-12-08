from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE

client = TestClient(app)

def setup_function():
    STORE.clear()

def _h(user="u1", tenant="t1", role="intern"):
    return {"X-User": user, "X-Tenant": tenant, "X-Role": role}

def test_ingest_requires_principal():
    r = client.post("/ingest", json={"title": "a", "body": "b"})
    assert r.status_code == 401
    assert r.json()["detail"]["reason_code"] == "MISSING_PRINCIPAL"

def test_ingest_rejects_tenant_id_in_payload():
    """
    The Trap: User tries to sneak 'tenant_id' into the JSON.
    System detects it and explicitly fails with forbidden.
    """
    r = client.post(
        "/ingest",
        headers=_h(),
        json={"title": "a", "body": "b", "tenant_id": "spoof"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["reason_code"] == "TENANT_FIELD_FORBIDDEN"

def test_intern_cannot_ingest_admin_classification():
    r = client.post(
        "/ingest",
        headers=_h(role="intern"),
        json={"title": "a", "body": "b", "classification": "admin"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["reason_code"] == "CLASSIFICATION_FORBIDDEN"

def test_ingest_derives_tenant_from_principal_and_stores_doc():
    r = client.post(
        "/ingest",
        headers=_h(tenant="tenant_A", role="intern"),
        json={"title": "hello", "body": "world", "classification": "internal"},
    )
    assert r.status_code == 200
    doc_id = r.json()["doc_id"]
    assert r.json()["tenant_id"] == "tenant_A"
    assert r.json()["classification"] == "internal"

    stored = STORE.get_doc("tenant_A", doc_id)
    assert stored is not None
    assert stored.tenant_id == "tenant_A"
    assert stored.title == "hello"
    assert stored.body == "world"
    assert stored.classification.value == "internal"

def test_ingest_invalid_classification_is_400():
    r = client.post(
        "/ingest",
        headers=_h(),
        json={"title": "a", "body": "b", "classification": "superadmin"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["reason_code"] == "INVALID_CLASSIFICATION"