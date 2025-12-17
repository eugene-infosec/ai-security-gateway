# AI Security Gateway
> **Status:** v0.3.0 - Deployed dev slice (Lambda + API Gateway + alarms + deny receipts)

**A multi-tenant SaaS gateway that enables "AI-style retrieval" safely by enforcing non-negotiable security invariants.**

## ⚡ Quick Start

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
make install
```

## 🧾 Generate Deny Receipt (Local)

* **Run the API:**

```bash
make run-local
```

* **Trigger a 403 Forbidden:**
```bash
curl -i -X POST [http://127.0.0.1:8000/ingest](http://127.0.0.1:8000/ingest) \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
  ```

See evidence/E01_attack_receipt_local.png for the expected audit output.

## Proof (Security Invariant Regression Harness)

Run:
```bash
make gate
```

Expected:

PASS no_admin_leakage_gate

PASS tenant_isolation_gate

PASS safe_logging_gate

## Cloud Demo (Dev)

```bash
make doctor-aws
make deploy-dev
make smoke-dev
make logs-cloud
make destroy-dev
```

Evidence: see evidence/INDEX.md (E03–E05).
