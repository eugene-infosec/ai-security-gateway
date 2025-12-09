from fastapi.testclient import TestClient
from app.main import app
from app.logger import get_sink, clear_sink

client = TestClient(app)

def setup_function():
    clear_sink()

def test_deny_receipt_generated_on_403():
    """
    Thesis Proof: Attempting a forbidden action generates an immutable audit log.
    """
    # Intern tries to ingest Admin Doc (Forbidden)
    headers = {"X-User": "hacker", "X-Tenant": "tenant-a", "X-Role": "intern"}
    payload = {
        "title": "Hack",
        "body": "pwned",
        "classification": "admin"
    }
    
    r = client.post("/ingest", json=payload, headers=headers)
    assert r.status_code == 403
    
    # Verify the "Receipt" in the sink
    logs = get_sink()
    
    # We expect an "access_denied" event
    audit_logs = [l for l in logs if l.get("event") == "access_denied"]
    assert len(audit_logs) == 1
    
    receipt = audit_logs[0]
    assert receipt["reason_code"] == "CLASSIFICATION_FORBIDDEN"
    assert receipt["user"] == "hacker"
    assert receipt["role"] == "intern"
    assert receipt["status"] == 403
    
def test_audit_logs_never_contain_secrets():
    """
    Safety Proof: Even during a deny, we don't log the body.
    """
    headers = {"X-User": "hacker", "X-Tenant": "tenant-a", "X-Role": "intern"}
    payload = {
        "title": "Sensitive",
        "body": "MY_SECRET_PASSWORD", # <--- Should not appear in logs
        "classification": "admin"
    }
    
    client.post("/ingest", json=payload, headers=headers)
    
    # Scan ALL logs
    logs = get_sink()
    for entry in logs:
        log_str = str(entry)
        assert "MY_SECRET_PASSWORD" not in log_str