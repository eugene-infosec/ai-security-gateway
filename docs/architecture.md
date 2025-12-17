# Architecture
> Truth scope: accurate as of **v0.3.0**. Items marked **Planned** are not implemented yet.

## Goal
A multi-tenant gateway that enables “AI-style retrieval” while enforcing non-negotiable security invariants.

## Security invariants
These are enforced by code and continuously checked by `make gate`.

1) **No Admin Leakage**: non-admin roles must never retrieve admin-classified content.
2) **Strict Tenant Isolation**: Tenant A must never retrieve Tenant B data.
3) **Safe Logging**: logs must never contain raw request bodies/queries/auth headers.
4) **Evidence-over-Claims**: denials are traceable via `request_id` and are backed by numbered evidence.

## Local request flow (deterministic)
- Identity is provided via headers: `X-User`, `X-Tenant`, `X-Role`
- Middleware assigns a `request_id` and returns `X-Request-Id`
- Policy is evaluated **before** any action (auth-before-action)
- Storage is tenant-scoped (structural isolation)
- Logging is structured JSON (“deny receipts”)

## Cloud dev slice (AWS)
Deployed via Terraform:
- Lambda (Python 3.12)
- API Gateway HTTP API
- CloudWatch log retention (7d)
- CloudWatch alarms: errors, throttles, high denials
- Metric filter counts deny receipts from structured logs

## Proof hooks
- `make gate` runs:
  - `no_admin_leakage_gate`
  - `tenant_isolation_gate`
  - `safe_logging_gate`
- Evidence is indexed in `evidence/INDEX.md`.

**Planned (Phase 6):**
- JWT at the edge (API Gateway JWT authorizer)
- Principal derived from JWT claims in cloud
