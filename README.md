# AI Security Gateway

**Retrieval-Safety-as-Code:** a production-shaped multi-tenant gateway that makes *unauthorized retrieval* hard by construction.

> **Status:** **v0.5.0** - JWT at the edge (Cognito + API Gateway authorizer), deny receipts, security gates, ops guardrails, and **snippet redaction**.
> **Where it fits:** place this gateway between your app/LLM and your knowledge store; it becomes the single enforced path for retrieval + snippets in a multi-tenant system.
> **Design principle:** security decisions are **metadata-based**, not prompt-based; they depend on `Principal` + tenant scope + classification, not on what a user asks.

---

## What this is

## 🎬 See it in action (80s)

> **"Stop patching prompts. Start securing retrieval."**

[![Watch the Demo](evidence/E01_attack_receipt_local.png)](evidence/demo.mp4)

*Click the image above to watch the full architecture and attack demo (with audio).*

A production-shaped **retrieval gateway** for RAG-style systems. The intended use case is simple and realistic:

> **Teams building “chat over docs / RAG features” must call this gateway for retrieval (and snippets) instead of querying the document store directly.**

This gateway enforces **Auth-Before-Retrieval** inside a strict trust boundary and emits structured **deny receipts** for every blocked action.

In RAG, the common critical leak is not “the LLM,” it’s **retrieval fetching the wrong tenant or wrong role**. Once unauthorized text enters the context window, you can’t “unfetch” it. This project prevents that failure mode by enforcing scope *before* storage reads and snippet generation.

### Concrete scenario (what it blocks)

* An **intern in Tenant A** tries to retrieve:

  * an **admin-classified runbook**, or
  * **Tenant B’s roadmap**
* Result: **blocked (403)** + **deny receipt** with `request_id` + `reason_code` (auditable, screenshot-safe).

### Why lexical search (intentional)

Retrieval is currently **deterministic lexical scoring** on purpose: the thesis is the **security boundary and invariants**, not embeddings quality. Vector search can be added later **without changing the invariants**.

---

## Non-negotiable security invariants

These invariants are enforced by code and continuously checked by `make gate`:

1. **No Admin Leakage**
   Non-admin roles must never retrieve admin-classified content (titles/snippets/bodies).

2. **Strict Tenant Isolation**
   Tenant A must never retrieve Tenant B data (structural scoping in storage keys + server-side authority).

3. **Safe Logging**
   Logs must never contain raw request bodies/queries/auth headers/tokens.

4. **Evidence-over-Claims**
   Every denial is traceable via `request_id` and backed by numbered evidence artifacts.

5. **No Secret Egress via Snippets**
   Snippet output is redacted to prevent accidental secret leakage.

---

## Trust boundary

* **Untrusted inputs:** request headers/body, query text, stored document text, any client-supplied claims.
* **Trusted compute boundary:** principal derivation, policy evaluation, tenant scoping, snippet redaction, audit logging.

### Identity modes

* **Local dev:** deterministic header identity (`X-User`, `X-Tenant`, `X-Role`) for fast tests and demos.
* **Cloud dev:** **Cognito JWT authorizer at API Gateway**; Lambda derives `Principal` from verified claims.

---

## ⚡ Start here (2 minutes)

### 1) Run the proof harness (security gates)

```bash
make ci
# or: make gate
```

### 2) Trigger a deny receipt (local)

```bash
make run-local

# In another terminal:
curl -i -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
```

Result: HTTP 403 and a structured audit log in stdout (deny receipt).

### 3) Verify proof (evidence artifacts)

All claims are backed by screenshots in `evidence/INDEX.md` (highlights below).

| ID      | Proof Artifact                 | Claim                                 |
| ------- | ------------------------------ | ------------------------------------- |
| **E01** | `E01_attack_receipt_local.png` | Local deny receipt with `request_id`  |
| **E02** | `E02_gate_pass_local.png`      | Security gates passing locally        |
| **E04** | `E04_attack_receipt_cloud.png` | AWS CloudWatch deny receipt           |
| **E06** | `E06_jwt_whoami.png`           | JWT identity verification (`/whoami`) |
| **E08** | `E08_redaction_proof.png`      | Snippet redaction (secret scrubbing)  |

---

## 🗺️ Repo map

* `app/` - FastAPI app + Lambda handler
* `app/security/` - principal, policy, audit, JWT mapping, redaction engine
* `evals/` - security invariant regression harness (“security gates”)
* `infra/terraform/` - AWS dev slice (Lambda + HTTP API + Cognito + alarms)
* `docs/` - architecture, threat model, runbook, tradeoffs, decisions
* `evidence/` - numbered proof artifacts + index
* `tests/` - unit tests (incl. JWT principal + redaction)

---

## 🚀 Quick start (local)

**Prereqs:** Python 3.12+, `make`.

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
make doctor
make run-local
```

Verify liveness + identity:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/whoami \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'
```

---

## ☁️ Cloud dev slice (AWS + JWT)

**Prereqs:** AWS CLI configured, Terraform installed.

```bash
make doctor-aws
make deploy-dev

scripts/cognito_bootstrap_user.sh test-intern tenant-a intern
source scripts/auth.sh

make smoke-dev-jwt
make logs-cloud

make destroy-dev
```

> In the cloud, `/health` is public. All other routes require a valid JWT via the API Gateway authorizer.

---

## 🎬 Demo framing (2-10 minutes)

This is the quickest “real system” story to tell:

1. **Use case:** “Our app must call this gateway for retrieval instead of hitting the store directly.”
2. **Threat:** “Intern in Tenant A tries to retrieve admin runbook / Tenant B roadmap.”
3. **Result:** “Blocked before retrieval; deny receipt emitted; CI gates prevent regressions.”

For the full walkthrough: `docs/demo.md`.

---

## 📚 Documentation (truth-scoped)

* Architecture: `docs/architecture.md`
* Threat model: `docs/threat_model.md`
* Tradeoffs: `docs/tradeoffs.md`
* Runbook: `docs/runbook.md`
* Costs: `COSTS.md`
* Decisions (ADRs): `docs/decisions/`

---

## 💰 Cost safety (dev)

Designed to be cheap-by-default:

* serverless (Lambda scale-to-zero)
* short log retention (7 days)
* alarms for 5xx / throttles / high denials
* explicit kill switch: `make destroy-dev`
