# ADR 0002: Dual-Mode Identity (Local vs. Cloud)

## Context
We need to verify identity securely in the cloud (Zero Trust) but keep local development fast and deterministic (without mocking complex OIDC flows).

## Decision
We implement a **Dual-Mode Principal Resolver** behind a strict Invariant Boundary.
1. **Local (`AUTH_MODE=headers`)**: Identity is derived from `X-User`, `X-Tenant` headers.
2. **Cloud (`AUTH_MODE=jwt`)**: Identity is derived from cryptographically verified JWT claims passed by API Gateway.

## Consequences
- **Positive**: Local tests are fast (`make test` runs in milliseconds).
- **Positive**: Cloud security is absolute (Lambda never sees a request unless API Gateway validates the JWT signature).
- **Invariant**: The application logic relies solely on the `Principal` object, making the business logic agnostic to the auth method.
