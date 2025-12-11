# Changelog

All notable changes to this project will be documented in this file.

## [v0.3.0] - 2025-12-10
### Added
- Cognito + API Gateway JWT authorizer integration (JWT auth at the edge).
- Dual-mode principal resolver: header-based for local, JWT-based for cloud.
- JWT smoke test (`make smoke-dev-jwt`) and new evidence artifacts (`jwt_whoami.png`, `jwt_attack_receipt.png`).

### Changed
- Docs updated to reflect production-style identity (JWT claims → Principal).
- Audit logging wired to use `request.state.principal` for identity context.

## [v0.2.0] - 2025-12-09
### Added
- Cloud deployment to AWS Lambda + DynamoDB via Terraform.
- `make deploy-dev` / `make destroy-dev` flow for cost-safe demos.
- `make smoke-dev` to prove liveness, identity flow, and deny receipts in CloudWatch.

## [v0.1.1] - 2025-12-08
### Added
- **Unified Verification:** Added `make ci` target to run unit tests and security gates in one command.
- **CI Parity:** GitHub Actions pipeline now uses `make ci` to ensure local/cloud parity.
- **Evidence:** Consolidated proof artifacts (`attack_receipt.png`, `ci_gate_fail.png`) into the release.

## [v0.1.0] - 2025-12-08
### Released
- **Core Security Engine:** Implemented Auth-Before-Retrieval architecture.
- **Tenant Isolation:** Enforced structural isolation via tenant-scoped storage keys.
- **Audit System:** Added `deny_receipt` generation for 403 Forbidden events.
- **CI Gates:** Released `make gate` harness to prevent security regressions.
````