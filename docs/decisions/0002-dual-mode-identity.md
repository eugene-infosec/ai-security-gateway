# ADR 0002: Dual-Mode Identity (Local vs. Cloud)

> Truth scope: accurate as of **v0.6.0**.

## Context

The system needs two things at once:

* **Cloud security (zero-trust):** production-shaped identity must be cryptographically verified.
* **Local speed + determinism:** development and security gates should run without requiring an OIDC/JWT flow or external dependencies.

If local development requires “real auth” every time, iteration slows, and invariant gates become flaky or hard to run.

## Decision

Implement a **dual-mode Principal Resolver** behind a strict invariant boundary.

### Mode A - Local: `AUTH_MODE=headers`

* Identity is derived from explicit request headers:

  * `X-User`
  * `X-Tenant`
  * `X-Role`
* Used only for local demos/tests and deterministic security gates.

### Mode B - Cloud: `AUTH_MODE=jwt`

* Identity is derived from **verified JWT claims**.
* **API Gateway JWT authorizer (Cognito)** validates token signature and claims *before* Lambda is invoked.
* Lambda maps verified claims into the same internal `Principal` model (e.g., `sub`, `custom:tenant_id`, `custom:role`).

### Invariant boundary

After `Principal` derivation, the rest of the system (policy, scoping, retrieval, redaction, audit) is **auth-method agnostic** and relies only on the `Principal` object.

## Consequences

### Positive

* Local dev is fast and deterministic (unit tests + gates run without network dependencies).
* Cloud enforcement is production-shaped: unsigned/invalid tokens do not reach the application code path.
* Defense-in-depth remains intact: even in JWT mode, authorization decisions are still enforced in-app using `Principal`.

### Tradeoffs / Risks

* Two identity paths exist; mitigated by:

  * a single `Principal` model,
  * shared policy code paths after derivation,
  * tests covering both modes (including JWT principal mapping).

### Non-goals

* This ADR does not claim header identity is secure; it is explicitly a **local-only** convenience for deterministic verification.
