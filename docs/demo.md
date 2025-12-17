# Demo Script (2-12 minutes)
> Truth scope: accurate as of **v0.5.0**.

## What this project is (one sentence)
A multi-tenant retrieval gateway that enforces **auth-before-retrieval** and emits structured **deny receipts**, preventing unauthorized data from ever entering retrieval/snippet generation.

## Why it matters (the security reality)
Most RAG leaks aren’t “the LLM.” They’re retrieval pulling the wrong tenant or wrong role documents into context. Once unauthorized text is retrieved, you can’t “unfetch” it.

---

## Claims → Proof Map
- Architecture / trust boundary: `docs/architecture.md`
- Threat model: `docs/threat_model.md`
- Tradeoffs: `docs/tradeoffs.md`
- Evidence index: `evidence/INDEX.md`
- Executable proof:
  - `make gate` (security invariants)
  - `make ci` (tests + gates)

---

## Demo paths

### ✅ 2–3 minutes (fast)
1) Run the invariant harness: `make gate`
2) Trigger a deny receipt locally (403)
3) Point to the evidence index and explain `request_id` + `reason_code`

### ✅ 6–8 minutes (full)
Fast demo +:
- show tenant isolation (A cannot see B)
- show redaction proof (`E08`) for snippet output

### ✅ 10–12 minutes (deep)
Full demo +:
- explain “gates are misuse regression tests”
- explain safe logging contract (why body/query/auth never appear in logs)
- cloud JWT smoke test (`make smoke-dev-jwt`) + CloudWatch deny receipt

---

## Part 1 — Local (deterministic)

### 1) Run the security gates
```bash
make gate
```

**Expected:** `PASS` lines for:

* no admin leakage
* tenant isolation
* safe logging

**What it proves:** the security properties are continuously enforced and regressions are blocked.

### 2) Start the API

```bash
make run-local
```

### 3) Show identity + request correlation

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/whoami \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'
```

**Point out:**

* `request_id` exists for auditability
* identity is derived before sensitive operations run

### 4) Trigger a deny receipt (local)

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

### 5) Redaction proof (local)

Query a doc that contains a “secret-shaped” string and show it is redacted in the snippet.

**Reference:** `evidence/INDEX.md` (E08)

---

## Part 2 — Cloud dev (AWS + JWT)

### 1) Deploy

```bash
make doctor-aws
make deploy-dev
```

### 2) Create a test user + fetch JWT

```bash
scripts/cognito_bootstrap_user.sh test-intern tenant-a intern
source scripts/auth.sh
```

### 3) JWT smoke test (principal + deny receipt)

```bash
make smoke-dev-jwt
make logs-cloud
```

**Expected:**

* `/whoami` proves `Principal` derived from verified JWT claims
* unauthorized action triggers `403` + deny receipt in CloudWatch logs

**Reference:** `evidence/INDEX.md` (E06–E07)

### 4) Teardown (cost safety)

```bash
make destroy-dev
```
