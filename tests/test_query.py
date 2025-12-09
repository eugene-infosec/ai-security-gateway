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
    assert r.json()["reason_code"] == "MISSING_PRINCIPAL"

def test_no_admin_leakage_for_intern():
    ingest(h(tenant="A", role="admin"), "Payroll", "admin payroll SECRET_SHOULD_NEVER_APPEAR", "admin")
    ingest(h(tenant="A", role="admin"), "Handbook", "employee handbook", "internal")

    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "payroll"})
    assert r.status_code == 200
    results = r.json()["results"]
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

    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "roadmap"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 1
    assert "tenant a" in results[0]["snippet"].lower()

def test_snippet_redacts_canary_if_it_ever_appears():
    ingest(h(tenant="A", role="admin"), "Internal", "hello SECRET_SHOULD_NEVER_APPEAR world", "internal")
    r = client.post("/query", headers=h(tenant="A", role="intern"), json={"query": "hello"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert "[REDACTED]" in results[0]["snippet"]