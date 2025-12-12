# Design Trade-offs: Demo vs. Production

This document records architectural decisions made for the demo environment versus what would be required for a scaled production system.

## 1. Identity Management

- **Decision:** Use `X-User` headers for local dev; use Cognito JWTs for cloud.
- **Trade-off:** Headers allow deterministic, fast unit testing without mocking OIDC flows. Cognito provides real security in AWS.
- **Production:** Would enforce JWTs everywhere, potentially using a local OIDC emulator for dev.

## 2. Database Design

- **Decision:** Single DynamoDB table with `TENANT#{id}` partition keys.
- **Trade-off:** Simple infrastructure management (one table to deploy).
- **Production:** For strict compliance (GDPR/HIPAA), might require separate tables per tenant or per-item encryption keys (CMK).

## 3. Observability

- **Decision:** Structured logs + CloudWatch alarms on 5xx / denials / throttles.
- **Trade-off:** Sufficient for low-traffic demo and interviews.
- **Production:** Would require distributed tracing (e.g., X-Ray), sampling (1% success logging), and SLIs/SLOs defined in Datadog/Prometheus.