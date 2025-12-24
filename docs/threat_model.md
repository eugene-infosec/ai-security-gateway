# Threat Model

> Truth scope: accurate as of **v0.7.0**.

This document focuses on the project’s core security goal: **prevent unauthorized retrieval** (cross-tenant leakage and role-based leakage) and provide **auditable evidence** when the gateway blocks an action.

---

## 1) Assets

* **Tenant documents:** titles, snippets, bodies
* **Admin-classified documents:** higher sensitivity content that must never be exposed to non-admin roles
* **Identity context:** `Principal` (`user_id`, `tenant_id`, `role`)
* **Audit logs + metrics:** must not leak request contents, secrets, or tokens
* **Snippet output:** an egress channel that must not leak secrets

---

## 2) Trust boundaries

1. **Client → Gateway:** untrusted input (requests are attacker-controlled)
2. **Gateway policy engine:** trusted enforcement point (security decisions happen here)
3. **Store:** passive; the application must enforce scoping and authorization
4. **Logs/metrics:** must be safe, non-sensitive, and correlation-friendly
5. **Snippet/redaction layer:** must prevent “secret egress” from stored content

---

## 3) Threats, mitigations, and proof

### T1: Cross-tenant data leakage (BOLA)

**Threat:** Tenant A attempts to retrieve Tenant B content (intentionally or via bug).
**Mitigation:**

* Tenant is derived **server-side** (local headers for deterministic demos; JWT claims in cloud).
* All storage reads/writes are **tenant-scoped by construction** (no global scans in the store API).
  **Proof:** `evals/tenant_isolation_gate.py`

---

### T2: Admin data leakage to non-admin roles (IDOR / privilege bypass)

**Threat:** Non-admin roles retrieve admin-classified titles/snippets/bodies.
**Mitigation:**

* Role/classification authorization is enforced **before retrieval** and **before snippet generation**.
* Classification constraints are applied to retrieval scope (not “filter after fetch”).
  **Proof:** `evals/no_admin_leakage_gate.py`

---

### T3: Sensitive data leakage via logs

**Threat:** Request bodies, query text, auth headers/tokens, or secrets leak into logs (accidentally or via debug code).
**Mitigation:**

* Structured JSON logs with a strict **safe-logging allowlist**.
* Explicit exclusion of request bodies, queries, and auth material.
  **Proof:** `evals/safe_logging_gate.py`

---

### T4: Secret leakage via snippets (content egress)

**Threat:** Even when access is authorized, snippet output could accidentally leak secret-shaped strings (e.g., API keys) present in stored docs.
**Mitigation:**

* Regex-based snippet redaction on `/query` output to scrub secret-shaped patterns before egress.
  **Proof:** evidence artifact `E08_redaction_proof.png`

---

### T5: Abuse / DoS / unexpected load (cloud)

**Threat:** Traffic spikes (malicious or accidental) degrade availability or inflate cost.
**Mitigation:**

* API Gateway throttling at the edge.
* CloudWatch alarms for 5xx, throttles, and high denials.
* Fast teardown “kill switch” for dev: `make destroy-dev`.
  **Proof:** evidence artifacts for alarms + smoke tests (see `evidence/INDEX.md`)

---

### T6: Misconfiguration drift (cloud)

**Threat:** Manual changes or configuration drift weaken invariants, observability, or cost controls.
**Mitigation:**

* Terraform-managed infrastructure.
* Repeatable Make targets for deploy/smoke/destroy.
* Terraform formatting/validation as part of workflow/CI (where configured).
  **Proof:** reproducible `make deploy-dev` / `make smoke-dev-jwt` lifecycle + IaC in `infra/terraform/`

---

## 4) Residual risks and next steps (explicitly out-of-scope for v0.7.0)

* Stronger key management (AWS Secrets Manager / SSM Parameter Store for sensitive config)
* WAF + more nuanced rate limiting (per principal / per tenant)
* Per-tenant CMK / per-item envelope encryption (compliance-driven)
* Distributed tracing + SLIs/SLOs (beyond CloudWatch alarms and logs)
* More comprehensive DLP (beyond regex redaction; e.g., classification-aware policies, allowlists, or external scanners)
