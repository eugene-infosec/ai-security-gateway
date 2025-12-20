# Changelog

All notable changes to this project will be documented in this file.

This project follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`). Release dates are in **YYYY-MM-DD**.

---

## [v0.5.0] - 2025-12-17

### Added
* **Defense in Depth:** Regex-based snippet redaction engine (`app/security/redact.py`).
* **Security:** Redaction enforced on `/query` output to reduce secret egress risk.
* **Evidence:** `E08_redaction_proof.png`.

---

## [v0.4.0] - 2025-12-17

### Added
* **Identity (Cloud):** Cognito User Pool + Client for JWT issuance (custom claims: `tenant_id`, `role`).
* **Auth at the Edge:** API Gateway HTTP API JWT authorizer; `/health` public, all other routes require JWT.
* **Runtime Mode:** Lambda runs in `AUTH_MODE=jwt` and derives `Principal` from verified JWT claims.
* **Verification:** JWT smoke test target: `make smoke-dev-jwt`.
* **Evidence:** `E06_jwt_whoami.png`, `E07_jwt_attack_receipt_cloud.png`.

---

## [v0.3.0] - 2025-12-17

### Added
* **Cloud Deployment:** AWS dev slice via Terraform (Lambda + HTTP API).
* **Packaging:** Lambda artifact built to `dist/lambda.zip`.
* **Observability:** CloudWatch log retention + alarms (5xx errors, throttles, high denials) + deny metric filter.
* **Evidence:** `E03_smoke_dev_output.png`, `E04_attack_receipt_cloud.png`, `E05_alarms.png`.

---

## [v0.2.0] - 2025-12-16

### Added
* **Retrieval Endpoint:** `POST /query` with **auth-before-retrieval** scoping.
* **Storage (Local):** In-memory tenant-scoped store (structural isolation).
* **Security Gates:** `make gate` security invariant regression harness:
  * no admin leakage
  * tenant isolation
  * safe logging (no bodies/queries/auth headers in logs)
* **Evidence:** `E02_gate_pass_local.png`.

---

## [v0.1.0] - 2025-12-16

### Added
* **Foundation:** `.gitattributes`, `.gitignore`, pre-commit hooks, strict `Makefile`.
* **Identity (Local):** `Principal` model + header-based resolver.
* **Authorization:** Auth-before-action policy engine (`authorize_ingest`).
* **Auditability:** Structured audit logging with forensic deny receipts (`event=access_denied`).
* **Evidence:** `E01_attack_receipt_local.png`.
