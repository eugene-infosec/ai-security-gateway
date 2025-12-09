# Threat Model & Security Architecture

This document focuses on the primary security goal of this project:
**prevent unauthorized retrieval** (cross-tenant leakage and role-based leakage) and provide **auditable deny receipts**.

## 1. Core Assets
- **Tenant Data:** Documents stored and retrieved by the system.
- **Identity Context:** The derived `Principal` (user_id, tenant_id, role).
- **Audit Events:** Structured, append-only security-relevant events (e.g., `access_denied`) with correlation via `request_id`.

## 2. Trust Boundaries
- **API Boundary:** All incoming requests are attacker-controlled until a `Principal` is derived and policy is applied.
- **Invariant Boundary (Trusted Compute):** Principal derivation, policy evaluation, tenant scoping, snippet redaction, and audit logging.
- **Store Boundary:** Storage is passive; the app must enforce authorization and scoping before reads/writes.

> **Demo vs Production Identity:** Current deployments use **header-derived identity** for deterministic verification (`X-User`, `X-Tenant`, `X-Role`). A production deployment would derive identity from **JWT/authorizer claims** (no client-supplied roles).

## 3. Top Threats

| Threat | Mitigation Strategy | Evidence |
| :--- | :--- | :--- |
| **Cross-Tenant Leakage (BOLA)** | **Authority Derivation:** tenant is derived server-side (never accepted from request JSON). **Structural Isolation:** DynamoDB partitioning uses tenant-prefixed keys (`PK = TENANT#{tenant_id}`). | `evals/tenant_isolation_gate.py` |
| **Privilege Escalation / Admin Leakage (IDOR)** | **Role-Bounded Access:** interns cannot ingest `classification=admin`. **Auth-Before-Retrieval:** classification filtering is applied before ranking/snippet. | `evals/no_admin_leakage_gate.py`, `tests/test_ingest.py`, `tests/test_query.py` |
| **Sensitive Data in Logs** | **Safe Logging Contract:** structured allowlist; rejects unsafe keys and avoids logging bodies/queries/secrets. | `evals/safe_logging_gate.py`, `evals/safe_logging_gate.py` |
| **Prompt/Query Injection (Retrieval Manipulation)** | **Policy is metadata-based:** authorization depends on `Principal`, tenant scoping, and classification—not on the semantic content of prompts. **Snippet safety:** redaction prevents secrets from appearing even if stored. | `tests/test_query.py` (snippet redaction), CI gates (`make gate`) |

## 4. Residual Risks & Next Steps
- **DoS / Abuse:** Currently relies on API Gateway defaults + Lambda scaling. *Next:* API Gateway throttling, WAF, per-tenant rate limits.
- **Production Identity:** Demo uses header-auth. *Next:* JWT verification and/or API Gateway/Lambda authorizer; map claims to `Principal`.
- **Key Management / Secrets:** Minimal secrets today. *Next:* Secrets Manager / Parameter Store, KMS encryption policies where applicable.
- **Observability:** Add dashboards/alarms for deny rates, 4xx/5xx, latency, and cost (CloudWatch metrics + alarms).
