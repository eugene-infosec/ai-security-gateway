````markdown
# AI Security Gateway: Retrieval-Safety-as-Code

**A multi-tenant SaaS gateway that enables "AI-style retrieval" safely by enforcing non-negotiable security invariants.**

> **The Problem:** In RAG (Retrieval-Augmented Generation) systems, the hardest problem isn't the LLM, it's preventing the retrieval step from leaking admin data to interns, or Tenant A data to Tenant B.
>
> **The Solution:** A defense-in-depth gateway where authorization happens *before* retrieval, ensuring no unauthorized data ever enters the context window.

---

## ⚡ START HERE (2 Minutes)

If you are reviewing this for a role, these artifacts prove the claims:

1. **Architecture & Invariants**: [Read the Security Thesis](docs/architecture.md)
2. **The Proof (CI Gates)**: Run `make gate` (or `make ci`) to see the regression harness block Admin leakage and enforce Tenant Isolation.
3. **The Attack Receipt (Deny Receipt)**: Trigger a 403 and observe a structured audit log containing `event=access_denied`, `reason_code`, and `request_id` (example: `evidence/attack_receipt.png`).

### 🧾 How to Generate a Deny Receipt (Local)

Run the local API (`make run-local`) and trigger a policy violation:

```bash
# 1) Trigger a 403 (intern tries to create an admin-classified doc)
curl -i -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"I want admin access","classification":"admin"}'

# 2) Check server stdout for the structured audit receipt, e.g.:
# INFO:app:{"event":"access_denied","reason_code":"CLASSIFICATION_FORBIDDEN","tenant_id":"tenant-a","role":"intern","user":"malicious_intern","status":403,"path":"/ingest","request_id":"..."}
````

**Evidence artifacts**

* `evidence/attack_receipt.png` — deny receipt log line (403) with `request_id` + `reason_code`
* `evidence/ci_gate_fail.png` — an intentionally introduced regression being blocked by `make gate`
* `evidence/attack_receipt_cloud.png` — deny receipt from AWS (CloudWatch logs)
* `evidence/smoke_dev_output.png` — output from `make smoke-dev` against the deployed AWS endpoint

---

## 🛡️ Security Invariants (The "Why")

This system enforces four hard rules that cannot be bypassed by client code:

1. **No Admin Leakage**: An Intern role can never retrieve Admin-classified titles or snippets.
2. **Strict Tenant Isolation**: Tenant A can never retrieve Tenant B data (enforced by server-side authority derivation).
3. **Auth-Before-Retrieval**: Permissions are applied to the search scope, not filtered post-fetch.
4. **Evidence-Over-Claims**: Every deny is traceable via correlation ID; regressions are blocked by CI gates.

---

## 🚀 Quick Start

### Prerequisites

* Python **3.12+**
* AWS CLI (configured) — for cloud demo
* Terraform — for cloud demo

### Run Locally

```bash
# 1) Setup
python3 -m venv .venv && source .venv/bin/activate
make install

# 2) Verify environment
make doctor

# 3) Run the API
make run-local

# 4) Run tests + gates
make test
make gate
# or:
make ci
```

---

## ☁️ Cloud Demo (Dev)

This repo includes Terraform to deploy the Gateway to **AWS Lambda + DynamoDB** (serverless) and a smoke test that proves liveness, identity flow, and a deny receipt.

```bash
# 1) Verify AWS Identity
make doctor-aws

# 2) Package & Deploy (creates lambda_function.zip, then terraform apply)
make deploy-dev

# 3) Verify (hits /health and /whoami, then triggers a 403 deny)
make smoke-dev

# 4) Teardown (cost safety)
make destroy-dev
```

> **Security note:** The cloud demo intentionally uses a **header-based identity resolver** for easy verification (e.g., `X-User`, `X-Tenant`, `X-Role`). A production deployment would derive identity from **JWT/authorizer claims** instead of client-supplied role headers.

```
