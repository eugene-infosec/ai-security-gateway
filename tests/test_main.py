from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_returns_request_id():
    """
    Invariant: Every response must contain a correlation ID header and body field.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # Check body
    assert data["ok"] is True
    assert "request_id" in data
    assert len(data["request_id"]) > 0

    # Check header
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"] == data["request_id"]
