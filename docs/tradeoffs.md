# Tradeoffs
> Truth scope: accurate as of **v0.4.0**.

## Local identity vs Cloud identity
- Local uses header identity for deterministic demos and invariant tests.
- Cloud dev currently uses header identity (passed through API Gateway) for infra verification.
- **Planned:** JWT at the edge using API Gateway JWT authorizer and Cognito.

## Storage
- Current: in-memory store for speed + deterministic invariant gates.
- Tradeoff: not persistent across process restarts / instances.
- Planned: DynamoDB for persistence and multi-instance correctness.

## Retrieval
- Current: simple keyword scoring (demo-friendly).
- Tradeoff: not a true vector search, but still exercises the security boundary.
- Planned: vector retrieval while preserving invariants (auth-before-retrieval).

## Logging & observability
- Current: structured audit logs with strict no-leak rules.
- Tradeoff: less detailed debugging logs, but safer by default.

## Cloud scope
- Current: Production-shaped Principal from verified JWT claims.
