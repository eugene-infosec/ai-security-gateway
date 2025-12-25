# ADR 0002: Dual-Mode Identity (Local vs. Cloud)

> Truth scope: accurate as of **v0.9.0**.

## Context

The system needs two things at once:

* **Cloud security (zero-trust):** production-shaped identity must be cryptographically verified and rooted in a trusted source.
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

* Identity is derived from **verified, immutable JWT claims**.
* **API Gateway JWT authorizer (Cognito)** validates token signature and claims *before* Lambda is invoked.
* **Trust Anchor:** Custom attributes (`custom:tenant_id`, `custom:role`) are enforced as **immutable** (`mutable = false`) by the User Pool schema and cannot be written by the client.
* Lambda maps these verified claims into the same internal `Principal` model.

### Invariant boundary

After `Principal` derivation, the rest of the system (policy, scoping, retrieval, redaction, audit) is **auth-method agnostic** and relies only on the `Principal` object.

## Consequences

### Positive

* **Speed:** Local dev is fast and deterministic (unit tests + gates run without network dependencies).
* **Security:** Cloud enforcement is production-shaped; unsigned/invalid tokens do not reach the application code path.
* **Privilege Escalation Prevention:** Cloud identity claims are immutable, preventing compromised clients from elevating their own role/tenant (BOLA/IDOR protection).
* **Defense-in-depth:** Even in JWT mode, authorization decisions are still enforced in-app using the shared `Principal` logic.

### Tradeoffs / Risks

* Two identity paths exist; mitigated by:
  * a single `Principal` model,
  * shared policy code paths after derivation,
  * tests covering both modes (including JWT principal mapping).

### Non-goals

* This ADR does not claim header identity is secure; it is explicitly a **local-only** convenience for deterministic verification.
