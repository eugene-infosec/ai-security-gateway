# Controls Catalog (Controls → Implementation → Evidence)

> **Truth scope:** accurate as of **v1.0.0**.
> These controls are implemented as code paths + regression gates. Evidence is reproducible via `make verify` (alias: `make gate`).

This catalog is written to be **auditor-friendly**: each control maps to (1) the enforcement point in code, (2) a repeatable verification gate, and (3) a proof artifact (when applicable).

---

## C01 - Tenant Isolation

**Objective:** Prevent cross-tenant data retrieval and writes.

- **Implementation**
  - Retrieval and ingestion are structurally tenant-scoped:
    - `STORE.list_scoped(tenant_id=..., allowed_classifications=...)`
    - `STORE.put(tenant_id=..., classification=..., ...)`
  - Tenant identity is derived server-side (headers for deterministic local demos; verified JWT claims in cloud).

- **Regression Gate**
  - `evals/tenant_isolation_gate.py`

- **Evidence**
  - **E02** - Gate Pass (local)

---

## C02 - Pre-Retrieval Scope Enforcement

**Objective:** Ensure roles cannot retrieve unauthorized classifications (e.g., Intern → Admin). Enforce *Auth-Before-Retrieval*.

- **Implementation**
  - Allowed classifications are derived from the authenticated `Principal` role:
    - Example policy: `admin → {"public","admin"}`; non-admin → `{"public"}`
  - The scope is applied **before** any retrieval/search/snippet path runs:
    - `candidates = STORE.list_scoped(tenant_id=p.tenant_id, allowed_classifications=allowed)`

- **Regression Gate**
  - `evals/no_admin_leakage_gate.py`

- **Evidence**
  - **E01** - Local deny receipt (blocked admin-classified access)
  - **E07** - Cloud deny receipt (JWT mode)

---

## C03 - Safe Logging

**Objective:** Prevent leakage of sensitive data (tokens, raw query text, request bodies, secrets/PII-shaped strings) into telemetry.

- **Implementation**
  - Global safe logging controls prevent forbidden keys/values from being logged.
  - Query telemetry uses correlation-safe fields:
    - `query_sha256`, `query_len` (instead of raw query text)

- **Regression Gate**
  - `evals/safe_logging_gate.py`

- **Evidence**
  - **E02** - Gate Pass (local)

---

## C04 - Audit-Ready Deny Receipts

**Objective:** Maintain a forensic trail of denied access attempts with correlation IDs.

- **Implementation**
  - Centralized deny path emits a structured receipt:
    - `audit("access_denied", reason_code=..., request_id=..., tenant_id=..., role=..., user_id=..., status=403, path=...)`
  - Receipts are designed to be parsable by SIEM tools and correlatable via `request_id`.

- **Regression Gate**
  - Covered implicitly by enforcement in gates; deny-path behavior is exercised by:
    - `evals/no_admin_leakage_gate.py` (deny scenario)
    - `evals/tenant_isolation_gate.py` (deny scenario, if applicable)

- **Evidence**
  - **E01** - Local deny receipt
  - **E04** - CloudWatch deny receipt

---

## C05 - Egress Redaction

**Objective:** Prevent secret leakage via valid snippet output (content egress risk).

- **Implementation**
  - Snippet/title output is redacted before return:
    - `redact_text(d.title)`
    - `redact_text(d.body)[:160]`
  - Redaction is deterministic and intentionally lightweight for demo reproducibility.

- **Regression Gate**
  - Verified via evidence artifact; optionally exercised via targeted tests depending on repo setup.

- **Evidence**
  - **E08** - Redaction proof

---

## How to re-verify (one command)

```bash
make verify
# alias: make gate
```

**Expected:** passes for tenant isolation, admin leakage prevention, safe logging, and supply-chain audit (`pip-audit`).
