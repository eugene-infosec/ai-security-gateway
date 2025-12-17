## [0.3.0] - 2025-12-17
### Added
- AWS dev deployment via Terraform (Lambda + HTTP API).
- Lambda packaging to `dist/lambda.zip`.
- CloudWatch log retention + alarms (errors, throttles, high denials) + deny metric filter.
- Evidence: `E03_smoke_dev_output.png`, `E04_attack_receipt_cloud.png`, `E05_alarms.png`.

## [0.2.0] - 2025-12-16
### Added
- Local retrieval endpoint `POST /query` with auth-before-retrieval scoping.
- In-memory tenant-scoped store (structural isolation).
- Security invariant regression harness (`make gate`):
  - no admin leakage
  - tenant isolation
  - safe logging (no bodies/queries/auth headers in logs)
- Evidence: `E02_gate_pass_local.png`

## [0.1.0] - 2025-12-16
### Added
- **Foundation**: `.gitattributes`, `.gitignore`, pre-commit hooks, strict Makefile.
- **Identity**: `Principal` model, header-based resolver.
- **Security**: Auth-Before-Action policy engine (`authorize_ingest`).
- **Observability**: Structured audit logging with forensic deny receipts (`event=access_denied`).
- **Evidence**: `E01_attack_receipt_local.png`.
