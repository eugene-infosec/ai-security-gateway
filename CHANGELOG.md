# Changelog

All notable changes to this project will be documented in this file.

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