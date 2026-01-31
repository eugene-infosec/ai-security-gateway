import logging
from fastapi.testclient import TestClient
from app.main import app
from app.store import STORE

client = TestClient(app)


def test_intern_cannot_ingest_admin_and_emits_deny_receipt(caplog):
    STORE.clear()
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

    # 2. Assert Audit Contract
    # Filter for the audit record
    audit_records = [rec for rec in caplog.records if rec.name == "app.audit"]
    assert audit_records, "Expected a structured audit receipt"

    rec = audit_records[-1]

    # Check 'props' if using the new structured logging pattern
    if hasattr(rec, "props"):
        payload = rec.props
    else:
        # Fallback if message itself is the dict (depends on call site)
        payload = rec.msg

    assert isinstance(payload, dict)
    assert payload["event"] == "access_denied"
    assert payload["reason_code"] == "CLASSIFICATION_FORBIDDEN"
    assert payload["user_id"] == "malicious_intern"
    assert payload["schema_version"] == "1.0"
