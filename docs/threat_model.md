# Threat Model & Security Architecture

## 1. Core Assets
* **Tenant Data:** Proprietary documents stored in the system.
* **Identity Context:** The `Principal` object (User, Tenant, Role).
* **Audit Logs:** Immutable records of access and denial.

## 2. Trust Boundaries
* **The API Edge:** Any data entering `POST /ingest` or `POST /query` is untrusted until validated against the Principal.
* **The Store Boundary:** The storage layer is passive; the application must enforce scoping before reading/writing.

## 3. Top Threats
| Threat | Mitigation Strategy | Evidence |
| :--- | :--- | :--- |
| **Cross-Tenant Leakage** (BOLA) | **Authority Derivation:** Tenant ID is derived from the JWT/Header, never the payload. <br> **Structural Isolation:** Storage keys are tenant-prefixed. | `evals/tenant_isolation_gate.py` |
| **Privilege Escalation** (IDOR) | **Role-Bounded Access:** Interns cannot set `classification=admin`. <br> **Auth-Before-Retrieval:** Search scope is filtered *before* scoring. | `evals/no_admin_leakage_gate.py` |
| **Secret Leakage in Logs** | **Safe Logging Contract:** Allowlist schema filters out `body`, `query`, and `Authorization` headers. | `evals/safe_logging_gate.py` |
| **Prompt Injection** | **Metadata Filtering:** Security logic relies on structured metadata, not semantic meaning. "Ignore instructions" commands are ignored by the auth filter. | `evals/misuse_suite.py` |

## 4. Residual Risks & Next Steps
* **DDoS:** Currently mitigated only by Lambda concurrency limits. *Next Step:* WAF + API Gateway Throttling.
* **Key Management:** Currently using env vars/headers. *Next Step:* AWS Secrets Manager + IRSA.