from fastapi.testclient import TestClient
from app.main import app
from app.store import STORE

client = TestClient(app)

def setup_function():
    STORE.clear()

def h(user="u1", tenant="t1", role="intern"):
    return {"X-User": user, "X-Tenant": tenant, "X-Role": role}

def ingest(headers, title, body, classification):
    r = client.post("/ingest", headers=headers, json={
        "title": title, "body": body, "classification": classification
    })
    assert r.status_code == 200
    return r.json()["doc_id"]

def test_query_requires_principal():
    r = client.post("/query", json={"query": "x"})
    assert r.status_code == 401
    assert r.json()["detail"]["reason_code"] == "MISSING_PRINCIPAL"

def test_no_admin_leakage_for_intern():
    # Ingest a trap document
    ingest(h(tenant="A", role="admin"), "Payroll", "admin payroll SECRET_SHOULD_NEVER_APPEAR", "admin")
    ingest(h(tenant="A", role="admin"), "Handbook", "employee handbook", "internal")

    # Intern searches for "payroll"
    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "payroll"})
    assert r.status_code == 200
    results = r.json()["results"]
    
    # Intern should NOT see the admin doc at all (filtered before scoring)
    assert all("Payroll" != x["title"] for x in results)

def test_admin_can_retrieve_admin_doc():
    ingest(h(tenant="A", role="admin"), "Payroll", "admin payroll data", "admin")

    r = client.post("/query", headers=h(tenant="A", role="admin"), json={"query": "payroll"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert any(x["title"] == "Payroll" for x in results)

def test_tenant_isolation_blocks_cross_tenant_results():
    ingest(h(tenant="A", role="admin"), "Roadmap", "tenant A roadmap", "internal")
    ingest(h(tenant="B", role="admin"), "Roadmap", "tenant B roadmap", "internal")

    # Tenant A searches
    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "roadmap"})
    assert r.status_code == 200
    results = r.json()["results"]
    
    # Should only see Tenant A
    assert len(results) == 1
    assert "tenant a" in results[0]["snippet"].lower()
    assert "tenant b" not in results[0]["snippet"].lower()

def test_snippet_redacts_canary_if_it_ever_appears():
    # Note: this doc is internal so intern IS allowed to see it...
    # BUT the body contains a secret.
    ingest(h(tenant="A", role="admin"), "Internal", "hello SECRET_SHOULD_NEVER_APPEAR world", "internal")

    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "hello"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert results
    
    # The snippet engine must catch the secret and redact it
    assert "SECRET_SHOULD_NEVER_APPEAR" not in results[0]["snippet"]
    assert "[REDACTED]" in results[0]["snippet"]