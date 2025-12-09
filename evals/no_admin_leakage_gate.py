import sys
from fastapi.testclient import TestClient
from app.main import app
from app.store import STORE

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
    ingest(h(tenant="A", role="admin"), "Payroll", "admin payroll SECRET_SHOULD_NEVER_APPEAR", "admin")
    results = query(h(tenant="A", role="intern"), "payroll")

    for x in results:
        if x.get("title") == "Payroll":
            print("FAIL no_admin_leakage_gate: admin title leaked")
            return 1
        if "SECRET_SHOULD_NEVER_APPEAR" in (x.get("snippet") or ""):
            print("FAIL no_admin_leakage_gate: canary leaked in snippet")
            return 1

    print("PASS no_admin_leakage_gate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())