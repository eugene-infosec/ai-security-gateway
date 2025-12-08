from fastapi.testclient import TestClient
from app.main import app

def test_health_sets_request_id_header_and_body():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert "X-Request-Id" in r.headers
    # Ensure the ID in the header matches the one in the JSON body
    assert r.json()["request_id"] == r.headers["X-Request-Id"]

def test_health_respects_incoming_request_id():
    c = TestClient(app)
    # Simulate a request from an upstream load balancer
    r = c.get("/health", headers={"X-Request-Id": "fixed-id-123"})
    assert r.headers["X-Request-Id"] == "fixed-id-123"
    assert r.json()["request_id"] == "fixed-id-123"