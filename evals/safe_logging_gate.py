#!/usr/bin/env python3
import logging
import sys
import json
from io import StringIO
from fastapi.testclient import TestClient

# Import the REAL setup to test the REAL filter
from app.main import app
from app.store import STORE

# Strings that must NEVER appear in the raw JSON output
FORBIDDEN_SUBSTRINGS = [
    "sk_live_",
    "Bearer",
    "SUPER_SECRET_QUERY",
    "cookie",
    "Authorization",
]


def fail(msg: str) -> None:
    print(f"❌ FAIL safe_logging_gate: {msg}")
    sys.exit(1)


def main() -> None:
    STORE.clear()

    # 1. Capture Global Stdout (Root Logger)
    capture_stream = StringIO()

    # Re-initialize logging pointing to our capture stream
    # This ensures we test the actual JsonFormatter + SafeLogFilter logic
    root = logging.getLogger()
    for h in root.handlers:
        root.removeHandler(h)

    # Re-use your actual app logic
    from app.json_logger import JsonFormatter, SafeLogFilter

    handler = logging.StreamHandler(capture_stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SafeLogFilter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    c = TestClient(app)

    print("🔍 Executing Safe Logging Gate...")

    # Scenario A: Log Injection via Header (String Pattern)
    c.get("/health", headers={"Authorization": "Bearer sk_live_EVIL_TOKEN"})

    # Scenario B: Log Injection via Body (Dict Pattern)
    c.post(
        "/ingest",
        headers={"X-User": "admin", "X-Tenant": "t1", "X-Role": "admin"},
        json={
            "title": "Hack",
            "body": "This contains a sk_live_SECRET inside the body",
            "classification": "public",
        },
    )

    # Scenario C: Log Injection via Query Param (String Pattern)
    c.post(
        "/query",
        headers={"X-User": "admin", "X-Tenant": "t1", "X-Role": "admin"},
        json={"query": "SUPER_SECRET_QUERY"},
    )

    # 2. Analyze Captured Logs
    raw_logs = capture_stream.getvalue()

    # Check 1: Did we crash?
    if not raw_logs:
        print("⚠️  Warning: No logs captured. Ensure app is logging.")

    # Check 2: Are forbidden strings present?
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in raw_logs:
            print(f"CAPTURED LOGS:\n{raw_logs}")
            fail(f"Leaked sensitive string: '{bad}'")

    # Check 3: Is it valid JSON?
    for line in raw_logs.strip().split("\n"):
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            fail(f"Log line is not valid JSON: {line}")

    print("✅ PASS: No sensitive patterns found in structured logs.")


if __name__ == "__main__":
    main()
