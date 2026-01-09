import sys
import httpx
import time

# Configuration: Matches 'make run-local' defaults
GATEWAY_URL = "http://localhost:8000"


def check(name, passed, trace_id, latency_ms):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status:<8} | {name:<25} | {latency_ms:>3}ms | {trace_id}")
    return passed


def run_simulation():
    print(f"🚀 Verifying Security Gateway Invariants ({GATEWAY_URL})...\n")
    print(f"{'STATUS':<8} | {'INVARIANT':<25} | {'LATENCY'} | {'TRACE_ID'}")
    print("-" * 65)

    all_passed = True

    with httpx.Client(base_url=GATEWAY_URL, timeout=5.0) as client:
        # 1. Service Liveness
        t0 = time.time()
        try:
            r = client.get("/health")
            lat = int((time.time() - t0) * 1000)
            passed = r.status_code == 200
            check("Service Liveness", passed, r.headers.get("X-Trace-Id", "N/A"), lat)
            if not passed:
                all_passed = False
        except Exception:
            check("Service Liveness", False, "N/A", 0)
            print("🚨 Gateway is down. Run 'make run-local' first.")
            sys.exit(1)

        # 2. Identity Resolution (Zero Trust)
        t0 = time.time()
        headers = {"X-User": "demo", "X-Tenant": "tenant-a", "X-Role": "intern"}
        r = client.get("/whoami", headers=headers)
        lat = int((time.time() - t0) * 1000)
        # Verify it actually resolved the right tenant
        passed = r.status_code == 200 and r.json().get("tenant_id") == "tenant-a"
        if not check("Identity Resolution", passed, r.headers.get("X-Trace-Id"), lat):
            all_passed = False

        # 3. Deny Receipt (The "Fail-Closed" Test)
        # Intern trying to INGEST Admin docs -> MUST be 403 Forbidden
        t0 = time.time()
        headers = {"X-User": "malicious", "X-Tenant": "tenant-a", "X-Role": "intern"}
        payload = {
            "title": "HACK",
            "body": "trying to write admin data",
            "classification": "admin",
        }
        r = client.post("/ingest", json=payload, headers=headers)
        lat = int((time.time() - t0) * 1000)

        passed = r.status_code == 403
        if not check(
            "Policy Enforcement (403)", passed, r.headers.get("X-Trace-Id"), lat
        ):
            all_passed = False

    print("-" * 65)
    if all_passed:
        print("\n✨ All Security Invariants Verified.")
        sys.exit(0)
    else:
        print("\n🚨 Verification Failed.")
        sys.exit(1)


if __name__ == "__main__":
    run_simulation()
