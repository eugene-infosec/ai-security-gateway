#!/usr/bin/env python3
from __future__ import annotations

import sys
from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE


def fail(msg: str) -> None:
    print(f"FAIL tenant_isolation_gate: {msg}")
    sys.exit(1)


def main() -> None:
    STORE.clear()
    c = TestClient(app)

    # Seed tenant-a doc
    r = c.post(
        "/ingest",
        headers={"X-User": "seed", "X-Tenant": "tenant-a", "X-Role": "admin"},
        json={
            "title": "TENANT_A_DOC",
            "body": "alpha_only_keyword",
            "classification": "public",
        },
    )
    if r.status_code != 200:
        fail(f"expected 200 seeding tenant-a, got {r.status_code}: {r.text}")

    # Seed tenant-b doc with unique keyword
    r = c.post(
        "/ingest",
        headers={"X-User": "seed", "X-Tenant": "tenant-b", "X-Role": "admin"},
        json={
            "title": "TENANT_B_DOC",
            "body": "bravo_only_keyword",
            "classification": "public",
        },
    )
    if r.status_code != 200:
        fail(f"expected 200 seeding tenant-b, got {r.status_code}: {r.text}")
    tenant_b_doc_id = r.json()["doc_id"]

    # Query as tenant-a for tenant-b keyword (must return 0)
    r = c.post(
        "/query",
        headers={"X-User": "internA", "X-Tenant": "tenant-a", "X-Role": "intern"},
        json={"query": "bravo_only_keyword"},
    )
    if r.status_code != 200:
        fail(f"expected 200 querying as tenant-a, got {r.status_code}: {r.text}")

    results = r.json()["results"]
    for item in results:
        if item.get("doc_id") == tenant_b_doc_id:
            fail("tenant-b doc_id appeared in tenant-a results")
        if "TENANT_B_DOC" in item.get("title", ""):
            fail("tenant-b title appeared in tenant-a results")

    print("PASS tenant_isolation_gate")


if __name__ == "__main__":
    main()
