# Evidence Artifact Index (v1.0.0)

> **Truth scope:** accurate as of **v1.0.0**.
> **Traceability:** Every claim is backed by an artifact ID and a referenced file path.
> **Integrity:** See `E11` for SHA-256 hashes of all artifacts to ensure tamper-evidence.

---

### 🔐 Domain: Authentication & Identity
*Verification of Zero Trust invariants and Principal resolution.*

| ID  | File | Environment | Type | Claim / Proof |
| :-- | :--- | :--- | :--- | :--- |
| **E06** | `E06_jwt_whoami.png` | AWS (Dev) | Auth Verify | **Zero Trust Identity:** `/whoami` shows principal derived from verified JWT claims (not client headers). |
| **E07** | `E07_jwt_attack_receipt_cloud.png` | AWS (CloudWatch) | Logs | **JWT Deny Audit:** Authenticated deny produces CloudWatch receipt with `reason_code` + `request_id` (audit correlation). |

### 🛡️ Domain: Security Controls & DLP
*Verification of Fail-Closed behaviors, Redaction, and Access Control.*

| ID  | File | Environment | Type | Claim / Proof |
| :-- | :--- | :--- | :--- | :--- |
| **E01** | `E01_attack_receipt_local.png` | Local | Runtime Receipt | **403 Deny Receipt:** Structured receipt emitted on access denied (`event=access_denied`, `reason_code`, `request_id`). |
| **E04** | `E04_attack_receipt_cloud.png` | AWS (CloudWatch) | Logs | **Cloud Deny Receipt:** CloudWatch log contains correlatable receipt for access denied (audit trail exists in cloud runtime). |
| **E08** | `E08_redaction_proof.png` | Local / AWS | DLP Proof | **Egress Redaction:** Secret/canary is replaced with `[REDACTED]` in returned snippet (no sensitive egress). |
| **E09** | `E09_fail_closed.png` | Local | Behavior | **Secure Defaults:** App refuses to start (or returns 500) if insecure headers are used without explicit dev flags. |

### 📊 Domain: Observability & Operations
*Verification of Guardrails, Alarms, and System Health.*

| ID  | File | Environment | Type | Claim / Proof |
| :-- | :--- | :--- | :--- | :--- |
| **E03** | `E03_smoke_dev_output.png` | AWS (Dev) | Smoke Output | **Cloud Smoke:** Deployed endpoint passes smoke (`make smoke-cloud`): health, identity, and deny-path behavior validated. |
| **E05** | `E05_alarms.png` | AWS (CloudWatch) | Config | **Operational Guardrails:** Alarms configured for 5xx errors, throttles, and elevated deny rates. |

### 🏗️ Domain: Supply Chain & CI/CD
*Verification of Build Integrity and Policy-as-Code.*

| ID  | File | Environment | Type | Claim / Proof |
| :-- | :--- | :--- | :--- | :--- |
| **E02** | `E02_gate_pass_local.png` | Local | Test Output | **Gate Pass:** Misuse regression suite passes (`make gate`): verifies no-admin-leakage, tenant isolation, safe logging. |
| **E10** | `E10_ci_pipeline.png` | GitHub Actions | CI Policy | **CI Enforcement:** Pipeline runs linters, tests, and security gates on every push (policy-as-code evidence). |
| **E11** | `E11_artifact_hashes.txt` | N/A | Integrity | **Artifact Integrity:** SHA-256 hashes for all evidence files (supports external review and tamper-evidence). |
