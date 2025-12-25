# Cost Analysis and Operational Guardrails

> Truth scope: accurate as of **v0.9.0** (production-shaped).

This repo is designed to be **cheap-by-default** (serverless, short log retention, fast teardown). The removal of persistent storage (DynamoDB) in favor of ephemeral in-memory state for the demo further ensures zero idle storage costs.

---

## Estimated run rate (idle)

| Service                | Assumption                              | Est. Cost             |
| :--------------------- | :-------------------------------------- | :-------------------- |
| Lambda                 | Free tier likely covers idle demo usage | $0.00                 |
| API Gateway (HTTP API) | Free tier likely covers demo usage      | $0.00                 |
| Cognito                | MAU free tier likely covers demo users  | $0.00                 |
| CloudWatch             | Logs + a few alarms; 7-day retention    | Low (typically cents) |
| **Total** | Dev demo usage                          | **~<$1 / month** |

> Actual cost depends on request volume, log volume, and regional pricing. For longer testing, use **AWS Billing** / **Cost Explorer**.

---

## Operational guardrails

1. **Kill switch:** `make destroy-dev` destroys dev infra immediately.
2. **Log retention:** 7 days to cap storage cost.
3. **Alarms:** 5xx errors, throttles, high denials.
4. **Throttling:** enforced at the edge (API Gateway) to reduce abuse risk.
