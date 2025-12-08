import pytest
from app.logger import log_safe

def test_log_safe_rejects_unsafe_keys():
    """
    Crucial Security Test:
    Ensures that if a developer accidentally tries to log 'body' or 'password',
    the application raises an error immediately.
    """
    with pytest.raises(ValueError) as excinfo:
        log_safe({"event": "x", "request_id": "1", "body": "NOPE"})
    
    assert "Unsafe log keys" in str(excinfo.value)