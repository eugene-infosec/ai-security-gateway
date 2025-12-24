# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.8.0] - 2025-12-24

### Security Hardening (Golden Build)
* **Identity Boundary:** Enforced immutability on Cognito `tenant_id` and `role` attributes (`mutable = false`) and removed write permissions from the client to prevent privilege escalation.
* **Safe Logging:** Implemented a global `SafeLogFilter` in `app/json_logger.py` to intercept and block sensitive keys (cookies, auth headers) from `stdout`, ensuring no leakage occurs even outside the audit subsystem.
* **Zero CVEs:** Removed vulnerable `python-jose` dependency and `starlette` (via `fastapi`) to resolve known high-severity vulnerabilities.

### Infrastructure & Operations
* **Reviewer Experience:** Added `make review` target to provide a guided summary of build status, security gates, and validation steps.
* **Reproducibility:** Fixed and standardized cloud workflow scripts (`scripts/package_lambda.py`, `scripts/smoke_cloud_jwt.py`), ensuring the cloud dev slice is fully deployable and testable.
* **Cleanup:** Removed dead `DynamoDBStore` implementation to align the codebase with the documented "In-Memory" tradeoff and reduce attack surface.

---

## [v0.7.0] - 2025-12-24

### Changed
* **Repo Hygiene:** Hardened `.gitignore` & removed local artifacts/state (venvs, dist artifacts, Terraform state) from accidental tracking.
* **Security Correctness:** Snippet generation now redacts full text before slicing (boundary-safe), with a regression test.
* **Observability:** Request correlation now safely honors upstream `X-Request-Id` and injects `request_id` into all JSON logs.
* **CI Alignment:** CI runs `make gate` which is fresh-machine friendly (bootstraps venv + runs full security gates).

### Added
* **Supply chain automation & check:** Dependabot configuration for weekly pip dependency update PRs; `pip-audit` included in gate.
* **Portability:** Minimal Dockerfile + `make docker-build` / `make docker-run` for running the local demo without installing Python tooling.
* **Documentation:** `docs/retrospective_v0.7.0.md` (issues found, why they matter, fixes shipped, tradeoffs acknowledged).

---

## [v0.6.0] - 2025-12-20

### Changed
* **Architectural Alignment:** Terraform configuration now explicitly reflects the `InMemoryStore` usage (removed unused DynamoDB resource) to ensure infrastructure honesty.
* **Makefile Standardization:** Renamed `smoke-dev` to `smoke-cloud` for clarity; added explicit `smoke-local` target.
* **Entry Point:** Consolidated Lambda entry point into `app.main.handler`; removed redundant `app/lambda_handler.py`.

### Added
* **Credibility Signals:** Added `LICENSE` (MIT), `SECURITY.md`, and a CI Status Badge to `README.md`.
* **Reviewer Path:** Added a "90-Second Review" guide to the README to streamline evaluation.
* **CI Target:** Added explicit `make ci` target mapping to `fmt lint sec test gate`.

### Removed
* **Dead Code:** Removed unused `app/middleware.py` and `app/lambda_handler.py`.
* **Unused Infra:** Removed `aws_dynamodb_table` from Terraform to align with the v0.6.0 reference architecture.

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
