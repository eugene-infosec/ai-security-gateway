````markdown
# ⚡ Interview Demo Script & Runbook — AI Security Gateway (Retrieval-Safety-as-Code)

This single file is intentionally **multi-purpose**:

1) **Interview script** (what to say, naturally, without sounding rehearsed)  
2) **Runbook** (exact commands, expected outputs, and what they prove)  
3) **Long-term memory aid** (so Future-You can re-explain the system in depth years later)

---

## What this project is (one sentence)

A multi-tenant **retrieval gateway** that enforces **Auth-Before-Retrieval** and emits **deny receipts**, ensuring unauthorized data never enters the retrieval or snippet-generation path.

## Why it matters (the security reality of RAG)

In Retrieval-Augmented Generation systems, the most common critical leak is **not** the LLM — it’s retrieval pulling the **wrong tenant** or **wrong role** documents into the context window.  
Once the system fetches unauthorized text, you can’t “unfetch” it. Any “filter later” model is **hope-based** and fails real audits.

---

## Claims → Proof Map (for reviewers)

If a reviewer reads only a few items, point them here:

- **Architecture / Trust boundaries:** `docs/architecture.md`
- **Threat model:** `docs/threat_model.md`
- **Evidence artifacts (screenshots):**
  - `evidence/attack_receipt.png` — local deny receipt example
  - `evidence/attack_receipt_cloud.png` — cloud deny receipt (CloudWatch)
  - `evidence/ci_gate_fail.png` — intentionally introduced regression blocked by `make gate`
  - `evidence/smoke_dev_output.png` — successful AWS smoke test output

The proof is executable:
- `make test` — unit tests
- `make gate` — security misuse regression suite (invariant gates)
- `make ci` — one-command verification (same command used in GitHub Actions)

---

## Demo paths (choose one)

### ✅ 2–3 minutes (fast)
1) Show `docs/architecture.md` (trust boundary + auth-before-retrieval)  
2) Run `make ci`  
3) Trigger a deny receipt (local or cloud) and point to `reason_code` + `request_id`

### ✅ 6–8 minutes (full)
Fast demo +:
- show tenant isolation (A cannot see B)
- explain deny receipt fields and why they exist
- state “demo identity vs production identity” honestly

### ✅ 10–12 minutes (deep)
Full demo +:
- explain gates as “misuse regression tests”
- explain safe logging contract (why body/query/auth never appear in logs)
- map threats → mitigations → evidence artifacts

---

# 🗣️ Part 1 — Interview Script (What to say)

Use this like a menu. Keep it natural; don’t memorize verbatim.

## 1) Hook (20–30s)
**Say:**  
“Most RAG systems fail security reviews because they fetch first and filter later. If anything in that chain slips, sensitive data enters the context window. I built a gateway that enforces **auth-before-retrieval**, and every denial produces a structured **deny receipt** you can audit.”

**Show:** `docs/architecture.md`

**Point out:**  
- principal derivation happens **before** retrieval/snippet generation  
- tenant authority is derived server-side (client cannot assert tenant)  
- classification enforcement happens before search results can be returned

## 2) What makes it “senior” (20–30s)
**Say:**  
“I treat security like code: explicit invariants, misuse tests, and evidence. I’m not asking you to trust me — everything is executable, and regressions are blocked in CI.”

**Show:** `make ci` and GitHub Actions using the same command.

## 3) Proof: misuse regression suite (30–45s)
**Say:**  
“These are adversarial tests that simulate real failure modes: admin leakage, cross-tenant leakage, and unsafe logging.”

**Run:** `make ci` (or `make gate`)

**Point out:**  
- gates validate security **properties**, not just endpoint success  
- the suite blocks regressions the moment they’re introduced

## 4) The attack + deny receipt (45–75s)
**Say:**  
“Security is invisible unless you can prove it. Here’s a policy violation and the deny receipt: who/what/when/why, plus a correlation ID.”

**Run:** local or cloud deny receipt command (below)

**Point out in output/logs:**  
- `event = "access_denied"`  
- `reason_code = "CLASSIFICATION_FORBIDDEN"` (example)  
- `request_id = "..."` (correlation)

## 5) Cloud proof (10–20s)
**Say:**  
“This isn’t just a local toy. Same logic runs on AWS Lambda with DynamoDB, deployed via Terraform, and the same invariants hold.”

**Show:**  
- `evidence/attack_receipt_cloud.png`  
- optionally `evidence/smoke_dev_output.png`

**Honesty note (important):**  
“The cloud demo uses header-derived identity for easy verification. In production, identity would come from JWT/authorizer claims — but the security shape stays the same.”

---

# 🛠️ Part 2 — Runbook (What to run)

## A) Local demo (deterministic, fast)

### A1) Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
make install
make doctor
````

### A2) Run the API

```bash
make run-local
```

### A3) Liveness + identity (new terminal)

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/whoami \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'
```

**Expected:**

* `/health` returns:

  * `{"ok":true,"request_id":"..."}`
* `/whoami` returns:

  * `{"user_id":"demo","tenant_id":"tenant-a","role":"intern"}`

**What it proves:**

* request correlation exists (`request_id`) for auditability
* identity is derived before sensitive operations run

### A4) Generate a local deny receipt (policy violation)

This proves the system blocks privilege escalation and emits structured evidence.

```bash
curl -i -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
```

**Expected:**

* HTTP status `403`
* server stdout includes a structured audit event with fields like:

  * `"event":"access_denied"`
  * `"reason_code":"CLASSIFICATION_FORBIDDEN"`
  * `"path":"/ingest"`
  * `"request_id":"..."`

**What to say (one sentence):**
“This is the deny receipt: a forensic record we can correlate to the request ID and the security decision.”

### A5) Run the security gates (misuse regression suite)

```bash
make ci
# or:
make gate
```

**Expected:**

* `PASS no_admin_leakage_gate`
* `PASS tenant_isolation_gate`
* `PASS safe_logging_gate`

**What each gate proves (plain English):**

* **no_admin_leakage_gate:** an intern cannot retrieve admin-classified docs/snippets
* **tenant_isolation_gate:** tenant A cannot retrieve tenant B results
* **safe_logging_gate:** logs never include forbidden keys (body/query/auth headers)

---

## B) Cloud demo (AWS Lambda + DynamoDB)

> **Security note:** Cloud demo uses header-derived identity for verification. Production would derive identity from JWT/authorizer claims.

### B1) Deploy

```bash
make doctor-aws
make deploy-dev
```

**Expected:**

* Terraform prints:

  * `base_url = "https://...execute-api...amazonaws.com"`

### B2) Verify (smoke test)

```bash
make smoke-dev
```

**Expected:**

* `/health` ok
* `/whoami` ok
* `403` triggered for deny receipt test
* output reminds you to check CloudWatch for `event=access_denied`

### B3) Find the deny receipt in CloudWatch (and screenshot it)

* CloudWatch Logs → log group: `/aws/lambda/ai-security-gateway-dev`
* Search for: `"event":"access_denied"`

Save screenshot as:

* `evidence/attack_receipt_cloud.png`

### B4) Teardown (cost hygiene)

```bash
make destroy-dev
```

---

# 🧠 “If asked…” answers (common questions)

## “Isn’t header auth insecure?”

Yes — and we explicitly say so.

* Header-derived identity is used **only** to make the demo easy to verify.
* In production, identity would come from trusted JWT/authorizer claims (Cognito/OIDC).
* The enforcement pattern remains:

  1. derive principal
  2. scope permissions
  3. retrieve only authorized records
  4. generate safe snippets
  5. emit auditable logs and deny receipts

## “Where is enforcement actually happening?”

At the invariant boundary:

* tenant is derived server-side (never trusted from JSON payload)
* role/classification is enforced **before** retrieval results are scored/snippeted
* logs follow an allowlist contract (no bodies, no queries, no auth headers)

## “What’s the difference between tests and gates?”

* Unit tests verify correctness in isolation.
* Gates are **misuse regression tests**:

  * simulate attacker-like inputs / real failure modes
  * guarantee those behaviors stay blocked in CI forever

## “How do you prove you blocked an attack?”

The deny receipt:

* `event = "access_denied"`
* `reason_code = "..."`
* `request_id = "..."`
* and in cloud: the same receipt exists in CloudWatch.

---

# 🔧 Troubleshooting (fast fixes)

## 1) Markdown rendering looks broken

**Symptom:** code blocks “bleed” into the rest of the page.
**Cause:** mismatched code fences.
**Fix:** every code block must open and close cleanly:

````text
```bash
# commands...
````

````

## 2) Local: `make test` passes but `make gate` fails
**Meaning:** unit tests are green, but a **security invariant** regressed.

Run:
```bash
make test
make gate
````

Common regressions:

* **Tenant scoping** (cross-tenant data visible)
* **Classification filtering** (intern sees admin-classified docs)
* **Snippet redaction** (canary/secret appears)
* **Safe logging** (forbidden keys appear in logs)

Where to look:

* `evals/no_admin_leakage_gate.py`
* `evals/tenant_isolation_gate.py`
* `evals/safe_logging_gate.py`

## 3) Cloud: `make smoke-dev` fails (or you see 5xx)

**Meaning:** Lambda/API is unhealthy or misconfigured.

Checks:

1. AWS identity:

```bash
make doctor-aws
```

2. Terraform outputs (confirm base URL):

```bash
cd infra/terraform && terraform output
```

3. CloudWatch logs:

* log group: `/aws/lambda/ai-security-gateway-dev`
* look for:

  * import/handler errors (packaging/path mismatch)
  * DynamoDB permission errors
  * missing env var (`TABLE_NAME`)

```