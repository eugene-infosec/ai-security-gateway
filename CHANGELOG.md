
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
