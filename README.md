# AI Security Gateway
> **Status:** v0.1.0 — Local deny receipt (policy + audit receipt)

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
