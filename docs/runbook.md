# Operational Runbook (Dev)
> Truth scope: accurate as of **v0.5.0**.

## 0) Preconditions
- Tooling: Python 3.12+, Make, AWS CLI, Terraform
- Use a non-root AWS identity (least privilege)

---

## 1) Local workflow
- Install: `make install`
- Environment check: `make doctor`
- Run: `make run-local`
- Tests + invariants: `make ci` (or `make test` + `make gate`)
- Required before commit: `make preflight`

---

## 2) Cloud dev workflow (AWS)
- Verify AWS identity: `make doctor-aws`
- Deploy: `make deploy-dev`
- Smoke test:
  - Header-mode (if supported): `make smoke-dev`
  - JWT-mode: `make smoke-dev-jwt`
- Tail logs: `make logs-cloud`
- Kill switch (cost safety): `make destroy-dev`

---

## 3) Observability

### Logs
- Destination:
  - Local: stdout
  - Cloud: CloudWatch Logs (Lambda)
- Retention: 7 days (Terraform)
- Logging policy: structured JSON; **no request bodies, queries, or auth tokens** in logs

### Alarms (Dev)
- 5xx errors (availability)
- throttles (abuse/load)
- high denials (security spikes)

---

## 4) What to do when an alarm fires
1) Check recent deploys/changes (commit/tag).
2) Inspect CloudWatch logs for:
   - `event="access_denied"` (security)
   - 5xx stack traces (availability)
   Use `request_id` to correlate.
3) If it’s a regression:
   - redeploy a known-good tag/commit
   - re-run `make smoke-dev-jwt`

---

## 5) Emergency procedures (“Break Glass”)
If Cognito / API Gateway is unavailable, do not add an app backdoor endpoint.
Use AWS IAM access to the data layer directly (DynamoDB), relying on CloudTrail for audit.

Example: force-delete a corrupted doc (illustrative; keys depend on your schema)

```bash
aws dynamodb delete-item \
  --table-name ai-security-gateway-dev-docs \
  --key '{"pk": {"S": "TENANT#A"}, "sk": {"S": "DOC#123"}}'
````

Guardrails:

* Use a dedicated admin role (MFA preferred).
* Document why/what was done.
