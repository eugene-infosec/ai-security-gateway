# Demo Script (2–12 minutes)

> Truth scope: accurate as of **v0.9.1**.

## Concrete use case (realistic)

Teams building RAG features must call this gateway for retrieval instead of querying the store directly.
It enforces **auth-before-retrieval** so **unauthorized text never enters retrieval/snippet generation** (and therefore never enters an LLM context window).

## One-sentence definition

A multi-tenant retrieval gateway that enforces **auth-before-retrieval** and emits structured **deny receipts**, preventing cross-tenant and role-based leakage while remaining auditable.

## Why it matters (security reality)

Most RAG leaks aren’t “the LLM.” They’re retrieval pulling the wrong tenant or wrong role documents into context. Once unauthorized text is retrieved, you can’t “unfetch” it. This project exists to lock down the retrieval boundary and prove it stays locked.
> **Note:** retrieval is intentionally **lexical** in this demo. The thesis is the **security boundary**, not embeddings. Vector search can be swapped in later without changing the invariants.

---

## Claims → Proof Map

* Architecture / trust boundary: `docs/architecture.md`
* Threat model: `docs/threat_model.md`
* Tradeoffs: `docs/tradeoffs.md`
* Evidence index: `evidence/INDEX.md`
* Executable proof:
  * `make gate` (security invariants + supply chain audit)
  * `make ci` (tests + gates)

---

## Demo paths

### ✅ 2-3 minutes (fast)

1. Show the problem in one sentence + the fix (“gateway must be called for retrieval”)
2. Run `make review` (guided build summary & status)
3. Run `make gate` (proof harness)
4. Trigger a deny receipt locally (403) and point to `request_id` + `reason_code`

### ✅ 6-8 minutes (full)

Fast demo +:

* show tenant isolation (Tenant A cannot see Tenant B)
* show redaction proof (`E08`) for snippet output

### ✅ 10-12 minutes (deep)

Full demo +:

* explain “gates are misuse regression tests” (they block regressions in CI)
* explain safe logging contract (no body/query/auth in logs)
* cloud JWT smoke test (`make smoke-cloud`) + CloudWatch deny receipt

---

# Part 1 - Local (deterministic)

## 0) The scenario you will narrate (keep repeating this)

* “An intern in **Tenant A** tries to retrieve **admin runbook** content → blocked.”
* “Tenant A tries to retrieve **Tenant B roadmap** content → blocked.”
* “Every block produces a **deny receipt** with a traceable `request_id`.”

## 1) Run the security gates (proof harness)

```bash
make gate

```

**Expected:** `PASS` lines for:

* no admin leakage
* tenant isolation
* safe logging
* supply chain security (`pip-audit`)

**What it proves:** security invariants are continuously enforced; regressions are blocked.

## 2) Start the API

```bash
make run-local

```

## 3) Show identity + request correlation

```bash
curl -s [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
curl -s [http://127.0.0.1:8000/whoami](http://127.0.0.1:8000/whoami) \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'

```

**Point out:**

* `request_id` exists for auditability (`X-Request-Id` / response field)
* identity is derived before sensitive operations run

## 4) Trigger a deny receipt (local)

This is the “you can screenshot this safely” moment.

```bash
curl -i -X POST [http://127.0.0.1:8000/ingest](http://127.0.0.1:8000/ingest) \
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

## 5) Tenant isolation (quick verbal + proof)

Say: “Even with the same role, Tenant A cannot retrieve Tenant B.”

Run the tenant isolation gate (already included in `make gate`) or call it out explicitly:

* `tenant_isolation_gate` PASS line
* optionally point to the evidence screenshot (if you have one)

## 6) Redaction proof (local)

Say: “Snippets are an egress channel, so I redact secret-shaped strings before they leave the gateway.”

Show the redacted output (live or via screenshot).

**Reference:** `evidence/INDEX.md` (E08)

---

# Part 2 - Cloud dev (AWS + JWT)

## 1) Deploy

**Note:** The new build system automatically handles packaging (no Docker required).

```bash
make doctor-aws
make deploy-dev

```

## 2) Create a test user + fetch JWT

```bash
scripts/cognito_bootstrap_user.sh test-intern tenant-a intern
source scripts/auth.sh

```

## 3) JWT smoke test (principal + deny receipt)

```bash
make smoke-cloud
make logs-cloud

```

**Expected:**

* `/whoami` proves `Principal` is derived from **verified JWT claims**
* unauthorized action triggers `403` + deny receipt in CloudWatch logs

**Reference:** `evidence/INDEX.md` (E06–E07)

> One sentence to say out loud:
> “Local identity is deterministic headers for gates; cloud identity is JWT at the edge. After derivation, the same invariants apply.”

## 4) Teardown (cost safety)

```bash
make destroy-dev
```
