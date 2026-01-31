# Operations

> Truth scope: accurate as of **v1.0.0**.
> Purpose: **Run, verify, demo, observe, and tear down** the dev slice safely.

## Table of contents

- [What this is](#what-this-is)
- [Claims → proof map](#claims--proof-map)
- [Quick start](#quick-start)
- [Demo script (2–12 minutes)](#demo-script-212-minutes)
- [Runbook (dev)](#runbook-dev)
- [Observability](#observability)
- [Costs & guardrails](#costs--guardrails)
- [Teardown (kill switch)](#teardown-kill-switch)

---

## What this is

### Concrete use case (realistic)

Teams building “chat over docs” / retrieval features must call **this gateway** for retrieval and snippets instead of querying the store directly.
It enforces **Auth-Before-Retrieval** so **unauthorized text never enters retrieval/snippet generation** (and therefore never enters an LLM context window).

### One-sentence definition

A multi-tenant **data access gateway** that enforces **identity-first scope before retrieval** and emits structured **deny receipts**, preventing cross-tenant and role/classification leakage while remaining auditable.

### Why it matters (security reality)

Most retrieval leaks aren’t “the LLM.” They’re the data layer pulling the wrong tenant or wrong role documents into memory/context. Once unauthorized text is retrieved, you can’t “unfetch” it. This project exists to lock down the retrieval boundary and prove it stays locked.

> Note: Retrieval is intentionally **lexical/deterministic** in this demo. The thesis is the **security boundary and invariants**, not embeddings quality. A vector store can be swapped in later without changing the invariants.

---

## Claims → Proof Map

- Architecture / trust boundary: `docs/architecture.md`
- Threat model: `docs/threat_model.md`
- Controls catalog (controls → implementation → evidence): `docs/controls.md`
- Evidence index: `evidence/INDEX.md`

**Executable proof**
- `make verify` (alias: `make gate`) - security invariants + supply chain audit
- `make ci` - same as gate (repo “truth” command)
- `make review` - guided reviewer summary / checklist

---

## Quick start

### Local (fastest)
```bash
make install
make doctor
make verify
make run-local
python examples/reference-client/verify.py
```

### Cloud dev (AWS + JWT)

```bash
make doctor-aws
make deploy-dev
make smoke-cloud
make logs-cloud
make destroy-dev
```

---

## Demo script (2–12 minutes)

### The scenario you will narrate (repeat this)

* “An intern in **Tenant A** tries to ingest/retrieve **admin-classified** content → blocked.”
* “Tenant A tries to retrieve **Tenant B** content → blocked.”
* “Every block produces a **deny receipt** with `reason_code` + traceable `request_id`.”

### ✅ 2–3 minutes (fast)

1. Say the problem + fix (one sentence): **“Retrieval must be scoped before any store read.”**
2. Run `make review` (guided reviewer summary)
3. Run `make verify` (proof harness / gates)
4. Run `python examples/reference-client/verify.py` (black-box contract: liveness + identity + policy)
5. Trigger a deny receipt locally (403 + `request_id`)

### ✅ 6–8 minutes (full)

Fast demo +:

* show tenant isolation (Tenant A cannot see Tenant B)
* show redaction proof (`E08`) for snippet output

### ✅ 10–12 minutes (deep)

Full demo +:

* explain “gates are misuse regression tests” (they block regressions in CI)
* explain safe logging contract (no body/query/auth in logs)
* cloud JWT smoke test (`make smoke-cloud`) + CloudWatch deny receipt

---

## Runbook (dev)

This runbook is optimized for **demos, verification, and safe teardown**.
It assumes the gateway is the *only* supported path for retrieval in the demo environment.

### 0) Preconditions

* Tooling: Python **3.12+**, `make`, AWS CLI, Terraform
* Use a **non-root** AWS identity (least privilege)
* Know your AWS region/environment prefix (as configured in Terraform/Make targets)

---

### 1) Local workflow (deterministic)

#### Install + verify toolchain

```bash
make install
make doctor
```

#### Verify controls (fast)

```bash
make verify
# (alias: make gate)
```

**Expected:** `PASS` lines for:

* tenant isolation
* no admin leakage
* safe logging
* supply chain security (`pip-audit`)

**What it proves:** invariants are continuously enforced; regressions are blocked.

#### Run the API

```bash
make run-local
```

#### Quick checks (liveness + principal derivation)

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/whoami \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'
```

Point out:

* `request_id` exists for auditability/correlation (`X-Request-Id` and `X-Trace-Id`)
* identity is derived **before** sensitive operations run
* local mode uses deterministic headers for fast gates and demos

#### Verification (client contract)

```bash
python examples/reference-client/verify.py
```

#### Trigger a deny receipt (local)

This is the “screenshot-safe” moment.

```bash
curl -i -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
```

**Expected:**

* HTTP `403`
* structured audit log emitted with:

  * `event="access_denied"`
  * `reason_code="CLASSIFICATION_FORBIDDEN"` (example)
  * `request_id="..."`

**Reference:** `evidence/INDEX.md` (E01)

#### Tenant isolation (optional explicit run)

You can either point to the `tenant_isolation_gate` PASS line from `make verify`, or run it explicitly:

```bash
AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true python -m evals.tenant_isolation_gate
```

#### Redaction proof (local)

Say: “Snippets are an egress channel, so I redact secret-shaped strings before they leave the gateway.”

Show it live (if you have a seeded secret) or point to the proof artifact.
**Reference:** `evidence/INDEX.md` (E08)

---

### 2) Cloud dev workflow (AWS + JWT)

#### Verify AWS identity + tooling

```bash
make doctor-aws
```

#### Deploy

Note: Deployment builds the Lambda artifact first (no Docker required).

```bash
make deploy-dev
```

#### Create a test user + fetch JWT

```bash
scripts/cognito_bootstrap_user.sh test-intern tenant-a intern
source scripts/auth.sh
```

#### JWT smoke test (principal + deny receipt)

```bash
make smoke-cloud
make logs-cloud
```

**Expected:**

* `/whoami` proves `Principal` is derived from **verified JWT claims**
* an unauthorized action triggers `403` + deny receipt in CloudWatch logs

**Reference:** `evidence/INDEX.md` (E06–E07)

One sentence to say out loud:

> “Local identity is deterministic headers for gates; cloud identity is JWT at the edge. After derivation, the same invariants apply.”

---

## Observability

### Logs

**Destination**

* Local: stdout
* Cloud: CloudWatch Logs (Lambda)

**Retention**

* 7 days (Terraform)

**Logging policy**

* Structured JSON
* Safe logging is enforced globally: never log request bodies, raw query text, auth headers/cookies, or tokens.
* Use `request_id` (returned as `X-Request-Id` and `X-Trace-Id`) for correlation.

### Alarms (dev)

CloudWatch alarms are configured for:

* **5xx errors** (availability)
* **throttles** (abuse/load)
* **high denials** (security spikes / misconfiguration)

### What to do when an alarm fires

1. **Check recent changes**

* Identify the last deployed commit/tag.

2. **Inspect CloudWatch logs**

* Filter for:

  * `event="access_denied"` (security)
  * 5xx stack traces (availability)
* Use `request_id` to correlate request → decision → outcome.

3. **If it’s a regression**

* Redeploy a known-good tag/commit.
* Re-run:

```bash
make smoke-cloud
```

4. **If it’s load/abuse**

* Confirm throttling metrics/alarm.
* Reduce traffic / verify caller behavior.
* Prefer correctness + safety: fail closed and preserve audit signals.

---

## Costs & guardrails

This repository is designed to be **cheap-by-default**: serverless compute, short log retention, and fast teardown.
The demo intentionally uses **ephemeral in-memory state** (no persistent data plane) to avoid idle storage costs.

### Cost model (what drives spend)

In the AWS dev slice, cost is primarily driven by:

* request volume (API Gateway + Lambda invocations)
* log volume (CloudWatch ingestion + retention)
* alarms/metrics (CloudWatch alarms + metric filters)

### Estimated run rate (idle / low usage)

| Service                | Assumption                                            | Est. cost         |
| :--------------------- | :---------------------------------------------------- | :---------------- |
| Lambda                 | Low request volume; free tier often covers demo usage | ~$0.00            |
| API Gateway (HTTP API) | Low request volume; demo traffic                      | ~$0.00–low        |
| Cognito                | Low MAU for test users                                | ~$0.00–low        |
| CloudWatch             | Structured logs + a few alarms; 7-day retention       | low (often cents) |
| **Total**              | Typical dev demo usage                                | **~<$1/month**    |

> Actual cost depends on request/log volume and region pricing. Verify via AWS Billing / Cost Explorer.

### Operational guardrails (implemented)

1. **Kill switch (teardown)**: `make destroy-dev`
2. **Short log retention**: 7 days
3. **Alarms for early warning**: 5xx, throttles, high denials
4. **Edge throttling (cost control)**: enforced at API Gateway

### Practical cost hygiene (recommended)

* Deploy only when needed: `make deploy-dev`
* Validate quickly: `make smoke-cloud` + `make logs-cloud`
* Tear down after review: `make destroy-dev`

---

## Teardown (kill switch)

### Cloud dev teardown

```bash
make destroy-dev
```

### State reset (dev)

This demo uses **ephemeral in-memory storage** to ensure reproducibility and zero idle cost. There is no persistent database to patch manually.

To clear state or recover from a bad deployment:

```bash
make destroy-dev
make deploy-dev
```

### Production scenario (reference)

In a real deployment with persistent storage (DynamoDB / vector DB):

1. Use a dedicated admin IAM role (MFA preferred).
2. Repair records via approved operational procedures (CLI/console + change control).
3. Preserve auditability:

   * CloudTrail for administrative actions
   * SIEM ingestion for gateway audit events (`request_id` correlation)
