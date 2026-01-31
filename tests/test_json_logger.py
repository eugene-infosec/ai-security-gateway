import logging
from app.json_logger import SafeLogFilter


def test_deeply_nested_secret_is_blocked():
    """
    Regression test: ensures SafeLogFilter recurses into nested dicts/lists
    and REDACTS secrets, rather than crashing or leaking.
    """
    filt = SafeLogFilter()

    # A standard log record with a deeply nested secret
    secret_value = "sk_live_1234567890abcdef"
    msg_payload = {"user": {"profile": {"metadata": {"api_key": secret_value}}}}

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg_payload,
        args=(),
        exc_info=None,
    )

    # ACT: Run the filter
    # It should return True (allow log) but mutate the record
    result = filt.filter(record)

    assert result is True

    # ASSERT: The secret is redacted in the message
    redacted_msg = record.msg
    metadata = redacted_msg["user"]["profile"]["metadata"]

    # Check Key Redaction (if "api_key" is sensitive key) OR Value Redaction
    # Based on our regex, "sk_live_..." matches the value pattern
    assert secret_value not in str(metadata)
    assert "[REDACTED_VALUE]" in str(metadata) or "[REDACTED_KEY]" in str(metadata)
