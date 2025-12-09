import sys
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.store import STORE

# --- SILENCE NOISE ---
# Only show WARNINGS or ERRORS. Hide INFO logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.WARNING)
# ---------------------

client = TestClient(app)

def h(user="u", tenant="A", role="admin"):
    return {"X-User": user, "X-Tenant": tenant, "X-Role": role}

def ingest(headers, title, body, classification):
    r = client.post("/ingest", headers=headers, json={
        "title": title, "body": body, "classification": classification
    })
    assert r.status_code == 200, r.text

def query(headers, q, k=10):
    r = client.post("/query", headers=headers, json={"query": q, "k": k})
    assert r.status_code == 200, r.text
    return r.json()["results"]

def main():
    STORE.clear()
    ingest(h(tenant="A", role="admin"), "Roadmap", "tenant A roadmap", "internal")
    ingest(h(tenant="B", role="admin"), "Roadmap", "tenant B roadmap", "internal")

    results = query(h(tenant="A", role="intern"), "roadmap")

    for x in results:
        if "tenant b" in (x.get("snippet") or "").lower():
            print("FAIL tenant_isolation_gate: tenant B content leaked")
            return 1

    print("PASS tenant_isolation_gate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())