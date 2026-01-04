import logging
import pytest
from app.json_logger import SafeLogFilter


def test_deeply_nested_secret_is_blocked():
    """
    Regression test: ensures SafeLogFilter recurses into nested dicts/lists
    to find secrets, rather than just checking top-level keys.
    """
    filt = SafeLogFilter()

    # A standard log record with a deeply nested secret
    # We use a pragma to tell detect-secrets this is intentional test data
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg={
            "user": {
                "profile": {
                    "metadata": {
                        "api_key": "sk_live_123"  # pragma: allowlist secret
                    }
                }
            }
        },
        args=(),
        exc_info=None,
    )

    with pytest.raises(ValueError) as exc:
        filt.filter(record)

    assert "Forbidden value" in str(exc.value)
