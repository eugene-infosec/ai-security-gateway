You’re 100% right to push back: **your current `docs/demo.md` is broken because of mismatched fences + duplicated sections**, and that’s why it “truncates” / collapses in GitHub’s renderer. That’s not a “content” problem — it’s a **Markdown correctness** problem.

Below is a **clean, comprehensive, future-proof `docs/demo.md`** that:

* renders correctly on GitHub (no broken fences),
* keeps your tone (“senior, natural”),
* includes **what + how + why** so “Future-You” can re-explain it in 3 years,
* stays consistent with your repo’s real commands (`make ci`, `make gate`, `make smoke-dev`, etc.),
* avoids fake links like `[http://...]` inside code blocks,
* adds **expected outputs**, “what to point at”, and “if asked” answers,
* includes a **proper Troubleshooting section** that actually renders.

Copy/paste this entire file as `docs/demo.md`:

````markdown
# ⚡ Interview Demo Script & Runbook (AI Security Gateway)

This file is designed to do three jobs at once:

1) **Performance Script** — what to say in an interview (short, natural, senior tone)  
2) **Runbook** — exact commands to run locally + in AWS  
3) **Memory Aid** — enough context that Future-You can explain it in depth years later

---

## What this project *is* (one sentence)

A multi-tenant “retrieval gateway” that enforces **Auth-Before-Retrieval** (and produces **deny receipts**) so unauthorized data never enters the retrieval/snippet path.

### Why this matters (2 sentences)
In RAG, the most dangerous leak is often **not the LLM** — it’s retrieval pulling the wrong tenant/role’s data into the context window.  
Once unauthorized text is fetched, you can’t “unsee” it, and post-filtering becomes a “hope-based” security model.

---

## “Claims → Proof” map (for reviewers)

If someone only reads 3 things, point them here:

- **Architecture / Trust boundaries:** `docs/architecture.md`
- **Threat model:** `docs/threat_model.md`
- **Evidence screenshots:**
  - `evidence/attack_receipt.png` — local deny receipt example
  - `evidence/attack_receipt_cloud.png` — cloud deny receipt example (CloudWatch)
  - `evidence/ci_gate_fail.png` — intentionally introduced regression blocked by `make gate`
  - `evidence/smoke_dev_output.png` — successful AWS smoke test output

The proof is executable:
- `make test` = unit tests
- `make gate` = security misuse regression suite
- `make ci` = one command that runs both (same as GitHub Actions)

---

## Demo paths (choose one)

### ✅ 2–3 minutes (fast)
1) Show `docs/architecture.md` (trust boundary + auth-before-retrieval)
2) Run `make ci`
3) Trigger a deny receipt (local OR cloud) and point at the structured log fields

### ✅ 6–8 minutes (full)
Fast demo +:
- show tenant isolation (Tenant A cannot see Tenant B)
- explain deny receipt fields (`reason_code`, `request_id`) and why they exist
- state “demo identity vs production identity” honestly

### ✅ 10–12 minutes (deep)
Full demo +:
- explain gates as “misuse regression tests”
- explain safe logging contract (why bodies/queries aren’t logged)
- map threats → mitigations → evidence artifacts

---

# 🗣️ Part 1 — Narrative Script (What to say)

Use this like a menu. Don’t memorize word-for-word; keep it natural.

## 1) Hook (20–30s)
**Say:**
“Most retrieval/RAG systems fail security reviews because they fetch first and filter later. If anything in that filter chain fails, sensitive data can enter the context window. I built a gateway that enforces **auth-before-retrieval**, and every denial produces an auditable receipt.”

**Show:**
- `docs/architecture.md`

**Point out:**
- principal derivation happens *before* retrieval/snippets
- tenant isolation is enforced server-side (no client authority)

## 2) What makes it “senior” (20–30s)
**Say:**
“I treat security like code: invariants, tests, and evidence. I’m not asking you to trust me — everything is executable, and regressions are blocked.”

**Show:**
- `make ci` exists and is used in GitHub Actions

## 3) Proof: misuse regression suite (30–45s)
**Say:**
“This runs adversarial tests that simulate the exact mistakes real systems make: admin leakage, cross-tenant leakage, and unsafe logging.”

**Run:**
- `make ci` (or `make gate`)

**Point out:**
- these gates are the “CI-enforced security contract”
- you’re testing *security properties*, not just endpoints

## 4) Attack + deny receipt (45–75s)
**Say:**
“Security is invisible unless you can prove it. Here’s a policy violation, and here’s the deny receipt: who/what/when/why, with a correlation ID.”

**Run:**
- deny receipt command (local or cloud)

**Point out in output/logs:**
- `event=access_denied`
- `reason_code=CLASSIFICATION_FORBIDDEN` (example)
- `request_id=...` (correlation)

## 5) Cloud proof (10–20s)
**Say:**
“This isn’t just a local toy; it’s deployed to AWS Lambda + DynamoDB via Terraform, with the same invariants.”

**Show:**
- `evidence/attack_receipt_cloud.png`
- optionally `evidence/smoke_dev_output.png`

**Honesty note (important):**
“The cloud demo uses header-based identity for easy verification; a production deployment would derive identity from JWT/authorizer claims.”

---

# 🛠️ Part 2 — Technical Runbook (What to run)

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

* `/health` returns something like:

  * `{"ok":true,"request_id":"..."}`
* `/whoami` returns principal JSON like:

  * `{"user_id":"demo","tenant_id":"tenant-a","role":"intern"}`

**What to explain:**

* `request_id` becomes the correlation key you can match with audit logs
* identity is derived before anything security-sensitive runs

### A4) Generate a local deny receipt (policy violation)

This proves the system blocks privilege escalation and emits structured evidence.

```bash
curl -i -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
```

**Expected:**

* HTTP status: `403`
* server stdout contains a structured audit line with:

  * `"event":"access_denied"`
  * `"reason_code":"CLASSIFICATION_FORBIDDEN"`
  * `"request_id":"..."`

**What to say:**

* “This is the deny receipt. It’s forensic: who/what/when/why + correlation id.”

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

**Explain in plain terms:**

* **no_admin_leakage_gate:** intern cannot retrieve admin-classified content
* **tenant_isolation_gate:** tenant A cannot retrieve tenant B content
* **safe_logging_gate:** logs never include forbidden keys like body/query/auth headers

---

## B) Cloud demo (AWS Lambda + DynamoDB)

> **Security note:** Cloud demo uses header-derived identity for verification. Production would use JWT/authorizer claims.

### B1) Deploy

```bash
make doctor-aws
make deploy-dev
```

**Expected:**

* Terraform prints an output like `base_url = "https://...execute-api....amazonaws.com"`

### B2) Verify (smoke test)

```bash
make smoke-dev
```

**Expected:**

* `/health` ok
* `/whoami` ok
* `403` triggered for deny receipt test
* output mentions CloudWatch logs for `event=access_denied`

### B3) Find the deny receipt in CloudWatch (and screenshot it)

* CloudWatch Logs → log group: `/aws/lambda/ai-security-gateway-dev`
* Search for: `"event":"access_denied"`

Save your screenshot as:

* `evidence/attack_receipt_cloud.png`

### B4) Teardown (cost hygiene)

```bash
make destroy-dev
```

---

# 🧠 “If asked…” answers (common interview questions)

## “Isn’t header auth insecure?”

Yes — and that’s why the README/demo explicitly calls it out.

* Header-based identity is used **only to make verification trivial** in the demo.
* In production, identity would come from trusted JWT/authorizer claims (Cognito/OIDC).
* The security *shape* stays the same:

  1. derive principal
  2. scope policy
  3. retrieve only authorized records
  4. generate safe snippet
  5. produce auditable logs

## “Where is security enforcement actually happening?”

At the invariant boundary:

* tenant is derived server-side (never from JSON payload)
* role/classification is enforced **before** retrieval results are scored/snippeted
* logs follow an allowlist contract (no bodies, no queries, no auth headers)

## “What’s the difference between tests and gates?”

* Unit tests verify correctness in isolation.
* Gates are **misuse regression tests**:

  * simulate attacker-like inputs / real failure modes
  * ensure those behaviors stay blocked permanently in CI

## “How do you prove you blocked an attack?”

The deny receipt:

* `event=access_denied`
* `reason_code=...`
* `request_id=...`
  And in cloud: the same receipt exists in CloudWatch.

---

## 🔧 Troubleshooting (fast fixes)

### 1) Markdown rendering looks broken

**Symptom:** Code blocks “bleed” into the rest of the page.

**Cause:** Mismatched code fences.

**Fix:** Every code block must start and end with triple backticks:

````text
```bash
# commands...
````
---

### 2) Local: `make test` passes but `make gate` fails
**Meaning:** Unit tests are green, but a **security invariant** regressed.

Run:
```bash
make test
make gate
````

If a gate fails, it’s usually one of these:

* **Tenant scoping** (cross-tenant data visible)
* **Classification filtering** (intern sees admin-classified docs)
* **Snippet redaction** (canary/secret appears in snippet)
* **Safe logging** (logs include forbidden keys like body/query/auth)

Where to look:

* `evals/no_admin_leakage_gate.py`
* `evals/tenant_isolation_gate.py`
* `evals/safe_logging_gate.py`

---

### 3) Cloud: `make smoke-dev` fails (or you see 5xx)

**Meaning:** The deployed Lambda/API is unhealthy or misconfigured.

Checks:

1. AWS creds & identity

```bash
make doctor-aws
```

2. Terraform outputs (confirm base URL)

```bash
cd infra/terraform && terraform output
```

3. CloudWatch logs

* Log group: `/aws/lambda/ai-security-gateway-dev`
* Look for:

  * import/handler errors (packaging path mismatch)
  * DynamoDB permission errors
  * missing env var (`TABLE_NAME`)

`````
