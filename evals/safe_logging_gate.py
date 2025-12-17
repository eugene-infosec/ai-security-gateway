#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
from io import StringIO
from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE

FORBIDDEN = (
    '"body"',
    '"query"',
    "Authorization",
    "authorization",
    "Cookie",
    "cookie",
    "sk_live_",  # simulate secret; must never appear in logs
    "SUPER_SECRET_QUERY_STRING",
)


def fail(msg: str) -> None:
    print(f"FAIL safe_logging_gate: {msg}")
    sys.exit(1)


def main() -> None:
    STORE.clear()
    c = TestClient(app)

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("app.audit")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        # Seed a doc whose BODY contains a secret-looking string (must not be logged)
        r = c.post(
            "/ingest",
            headers={"X-User": "seed", "X-Tenant": "tenant-a", "X-Role": "admin"},
            json={
                "title": "PUBLIC_WITH_SECRET",
                "body": "do not leak sk_live_1234567890ABCDE in logs",
                "classification": "public",
            },
        )
        if r.status_code != 200:
            fail(f"expected 200 ingest, got {r.status_code}: {r.text}")

        # Query with a very explicit secret query string (must not be logged)
        r = c.post(
            "/query",
            headers={"X-User": "intern1", "X-Tenant": "tenant-a", "X-Role": "intern"},
            json={"query": "SUPER_SECRET_QUERY_STRING"},
        )
        if r.status_code != 200:
            fail(f"expected 200 query, got {r.status_code}: {r.text}")

        # Trigger a deny (still must be safe)
        r = c.post(
            "/ingest",
            headers={
                "X-User": "malicious_intern",
                "X-Tenant": "tenant-a",
                "X-Role": "intern",
            },
            json={"title": "HACK", "body": "x", "classification": "admin"},
        )
        if r.status_code != 403:
            fail(f"expected 403 deny, got {r.status_code}: {r.text}")

    finally:
        logger.removeHandler(handler)

    logs = stream.getvalue()
    for bad in FORBIDDEN:
        if bad in logs:
            fail(f"forbidden content found in logs: {bad}")

    print("PASS safe_logging_gate")


if __name__ == "__main__":
    main()
