import logging
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_intern_cannot_ingest_admin_and_emits_deny_receipt(caplog):
    caplog.set_level(logging.INFO, logger="app.audit")

    r = client.post(
        "/ingest",
        headers={
            "X-User": "malicious_intern",
            "X-Tenant": "tenant-a",
            "X-Role": "intern",
        },
        json={"title": "HACK", "body": "x", "classification": "admin"},
    )

    # 1. Assert HTTP Contract
    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["reason_code"] == "CLASSIFICATION_FORBIDDEN"
    assert "request_id" in detail

    # 2. Assert Audit Contract (The Deny Receipt)
    # Filter for the raw records from the audit logger
    audit_records = [rec for rec in caplog.records if rec.name == "app.audit"]
    assert audit_records, "Expected a structured audit receipt"

    # CRITICAL FIX: The logger now receives a Dictionary object, not a string.
    # We access .msg directly.
    payload = audit_records[-1].msg

    # Validate the dictionary fields directly
    assert payload["event"] == "access_denied"
    assert payload["reason_code"] == "CLASSIFICATION_FORBIDDEN"
    assert payload["tenant_id"] == "tenant-a"
    assert payload["user_id"] == "malicious_intern"
    assert payload["status"] == 403
    assert payload["path"] == "/ingest"
    assert payload["request_id"] == r.headers["X-Request-Id"]


def test_admin_can_ingest_admin_classified():
    r = client.post(
        "/ingest",
        headers={"X-User": "admin1", "X-Tenant": "tenant-a", "X-Role": "admin"},
        json={"title": "OK", "body": "x", "classification": "admin"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["doc_id"]
    assert body["request_id"]
