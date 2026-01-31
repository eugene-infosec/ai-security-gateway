# ADR 0002: Dual-Mode Identity (Local vs. Cloud)

> Truth scope: accurate as of **v1.0.0**.

## Context

This system needs two properties at once:

- **Cloud security (zero-trust):** production-shaped identity must be cryptographically verified and rooted in a trusted source.
- **Local speed + determinism:** development and security gates should run without requiring an OIDC/JWT flow, external IdP dependencies, or network calls.

If local development requires “real auth” every time, iteration slows and invariant gates become flaky or hard to run for reviewers.

## Decision

Implement a **dual-mode Principal Resolver** behind a strict invariant boundary, controlled by `AUTH_MODE`.

### Mode A - Local: `AUTH_MODE=headers` (deterministic)

Identity is derived from explicit request headers:

- `X-User`
- `X-Tenant`
- `X-Role`

**Intended use:** local demos, unit tests, and deterministic security gates.

**Guardrail:** Header mode is intentionally **fail-closed by default** unless an explicit dev flag is set (e.g., `ALLOW_INSECURE_HEADERS=true`). This prevents accidental “header auth” in environments where it shouldn’t exist.

### Mode B - Cloud: `AUTH_MODE=jwt` (production-shaped)

Identity is derived from **verified JWT claims**.

- **API Gateway JWT authorizer (Cognito)** validates token signature and required claims *before* Lambda is invoked.
- Lambda derives the `Principal` from those verified claims.

**Trust anchor (claim integrity):**
- Security-relevant attributes (e.g., tenant/role) are controlled by the identity provider and are not writable by the client in normal application flows.
- The infrastructure configuration prevents client-side privilege escalation by restricting what the app client can write/update.

## Invariant boundary

After `Principal` derivation, the rest of the system is **auth-method agnostic** and relies only on the internal `Principal` object:

- policy evaluation
- tenant scoping
- auth-before-retrieval
- snippet redaction
- audit events / deny receipts

This ensures the security model does not depend on “where identity came from,” only that a valid `Principal` is present.

## Consequences

### Positive

- **Speed:** Local dev is fast and deterministic (tests + gates run without external dependencies).
- **Security:** Cloud enforcement is production-shaped; unsigned/invalid tokens do not reach the application code path.
- **Privilege escalation resistance:** Cloud identity attributes are rooted in the IdP configuration and are not client-asserted.
- **Defense-in-depth:** Even in JWT mode, authorization is still enforced in-app using the shared `Principal` policy logic.

### Tradeoffs / Risks

- Two identity paths exist.

**Mitigations**
- One `Principal` model shared across modes.
- Shared policy code paths after derivation.
- Tests/gates validate behavior in header mode; cloud smoke tests validate JWT principal mapping and deny receipts.

## Non-goals

- This ADR does **not** claim header identity is secure. It is explicitly a **local-only** convenience for deterministic verification and reviewer friendliness.
