# Threat Model & Security Architecture

This document focuses on the primary security goal of this project:
**prevent unauthorized retrieval** (cross-tenant leakage and role-based leakage) and provide **auditable deny receipts**.

## 1. Core Assets
- **Tenant Data:** Documents stored and retrieved by the system.
- **Identity Context:** The derived `Principal` (user_id, tenant_id, role).
- **Audit Events:** Structured, append-only security-relevant events (e.g., `access_denied`) with correlation via `request_id`.

## 2. Trust Boundaries
- **API & Identity Boundary:** All incoming requests are attacker-controlled.
  - **Local Dev:** Identity is mocked via headers (`X-User`, `X-Role`) for deterministic testing.
  - **AWS Production:** Identity is enforced at the edge by **Cognito + API Gateway JWT Authorizer**. The Lambda function only processes requests with valid, cryptographically signed claims.
- **Invariant Boundary (Trusted Compute):** Principal derivation, policy evaluation, tenant scoping, snippet redaction, and audit logging.
- **Store Boundary:** Storage is passive; the app must enforce authorization and scoping before reads/writes.

## 3. Top Threats

| Threat | Mitigation Strategy | Evidence |
| :--- | :--- | :--- |
| **Cross-Tenant Leakage (BOLA)** | **Authority Derivation:** tenant is derived server-side (from JWT in cloud, headers locally). **Structural Isolation:** DynamoDB partitioning uses tenant-prefixed keys (`PK = TENANT#{tenant_id}`). | `evals/tenant_isolation_gate.py` |
| **Privilege Escalation / Admin Leakage (IDOR)** | **Role-Bounded Access:** interns cannot ingest `classification=admin`. **Auth-Before-Retrieval:** classification filtering is applied before ranking/snippet. **JWT Verification:** Cloud requests must be signed by the trusted IdP (Cognito). | `evals/no_admin_leakage_gate.py`, `tests/test_principal_jwt.py` |
| **Sensitive Data in Logs** | **Safe Logging Contract:** structured allowlist; rejects unsafe keys and avoids logging bodies/queries/secrets. | `evals/safe_logging_gate.py` |
| **Prompt/Query Injection (Retrieval Manipulation)** | **Policy is metadata-based:** authorization depends on `Principal`, tenant scoping, and classification—not on the semantic content of prompts. **Snippet safety:** redaction prevents secrets from appearing even if stored. | `tests/test_query.py` (snippet redaction), CI gates (`make gate`) |

## 4. Residual Risks & Next Steps
- **Key Management / Secrets:** Minimal secrets today (relies on IAM/Env). *Next:* Secrets Manager / Parameter Store integration.
- **DoS / Abuse:** Currently relies on API Gateway defaults + Lambda scaling. *Next:* Implement API Gateway throttling and WAF (Phase 12).
- **Data Encryption:** DynamoDB encryption at rest (AWS owned key). *Next:* Customer Managed Keys (CMK) for per-tenant encryption.
- **Observability:** Cloud demo now has CloudWatch metric filters + alarms on:
  - high `access_denied` rate,
  - API 5xx errors,
  - API throttles.
  *Next:* add latency SLOs + dashboards (and wire alarms to SNS/Slack).