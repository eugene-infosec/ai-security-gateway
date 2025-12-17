#!/usr/bin/env python3
from __future__ import annotations

import sys
from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE


def fail(msg: str) -> None:
    print(f"FAIL no_admin_leakage_gate: {msg}")
    sys.exit(1)


def main() -> None:
    STORE.clear()
    c = TestClient(app)

    # Seed: admin doc in tenant-a (must be invisible to intern retrieval)
    r = c.post(
        "/ingest",
        headers={"X-User": "admin_seed", "X-Tenant": "tenant-a", "X-Role": "admin"},
        json={
            "title": "ADMIN_PAYROLL",
            "body": "admin payroll numbers",
            "classification": "admin",
        },
    )
    if r.status_code != 200:
        fail(f"expected 200 seeding admin doc, got {r.status_code}: {r.text}")
    admin_doc_id = r.json()["doc_id"]

    # Seed: public doc in same tenant (positive control)
    r = c.post(
        "/ingest",
        headers={"X-User": "admin_seed", "X-Tenant": "tenant-a", "X-Role": "admin"},
        json={
            "title": "PUBLIC_GUIDE",
            "body": "payroll basics for interns",
            "classification": "public",
        },
    )
    if r.status_code != 200:
        fail(f"expected 200 seeding public doc, got {r.status_code}: {r.text}")

    # Query as intern for "payroll"
    r = c.post(
        "/query",
        headers={"X-User": "intern1", "X-Tenant": "tenant-a", "X-Role": "intern"},
        json={"query": "payroll"},
    )
    if r.status_code != 200:
        fail(f"expected 200 querying, got {r.status_code}: {r.text}")

    results = r.json()["results"]
    for item in results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        doc_id = item.get("doc_id", "")

        if doc_id == admin_doc_id:
            fail("admin doc_id appeared in intern results")
        if "ADMIN_PAYROLL" in title or "ADMIN_PAYROLL" in snippet:
            fail("admin title/snippet appeared in intern results")

    print("PASS no_admin_leakage_gate")


if __name__ == "__main__":
    main()
