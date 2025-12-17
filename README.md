# AI Security Gateway
> **Status:** v0.4.0 - JWT at the edge (Cognito + API Gateway authorizer) + cloud deny receipts

**A multi-tenant SaaS gateway that enables "AI-style retrieval" safely by enforcing non-negotiable security invariants.**

## Docs (Truth-scoped)

These docs are accurate as of **v0.3.0** and will be updated only when features land.

- Architecture: `docs/architecture.md`
- Threat model: `docs/threat_model.md`
- Tradeoffs: `docs/tradeoffs.md`
- Runbook: `docs/runbook.md`
- Demo script: `docs/demo.md`
- Costs: `COSTS.md`

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
curl -i -X POST http://127.0.0.1:8000/ingest \
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

## Cloud Demo (Dev, JWT)

```bash
make doctor-aws
make deploy-dev

# 1) Create test user (Cognito)
scripts/cognito_bootstrap_user.sh test-intern tenant-a intern

# 2) Get JWT into your shell
source scripts/auth.sh

# 3) Prove JWT principal + deny receipt
make smoke-dev-jwt
make logs-cloud

# 4) Cost safety
make destroy-dev
```

Evidence: see evidence/INDEX.md (E06–E07).
