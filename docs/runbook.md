# Operational Runbook (Dev)

> Truth scope: accurate as of **v0.6.0**.

This runbook is optimized for **demos, verification, and safe teardown**. It assumes the gateway is the *only* supported path for retrieval in the demo environment.

---

## 0) Preconditions

* Tooling: Python **3.12+**, `make`, AWS CLI, Terraform
* Use a **non-root** AWS identity (least privilege)
* Know your AWS region/environment prefix (as configured in Terraform/Make targets)

---

## 1) Local workflow (deterministic)

### Install + verify

```bash
make install
make doctor
```

### Run the API

```bash
make run-local
```

### Quick checks

Liveness + principal derivation:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/whoami \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'
```

### Verification (tests + invariants)

```bash
make ci
# or:
make test
make gate
```

### Required before commit

```bash
make preflight
```

---

## 2) Cloud dev workflow (AWS)

### Verify AWS identity

```bash
make doctor-aws
```

### Deploy

```bash
make deploy-dev
```

### Smoke test

* **Cloud (JWT Mode - REAL):**
```bash
make smoke-cloud
```

* **Local (Header-mode):**

```bash
make smoke-local
```

### Tail logs

```bash
make logs-cloud
```

### Teardown (cost safety / “kill switch”)

```bash
make destroy-dev
```

---

## 3) Observability

### Logs

* **Destination**

  * Local: stdout
  * Cloud: CloudWatch Logs (Lambda)
* **Retention**

  * 7 days (Terraform)
* **Logging policy**

  * Structured JSON
  * **Never** log request bodies, query text, auth headers, or tokens
  * Use `request_id` for correlation

### Alarms (Dev)

* **5xx errors** (availability)
* **throttles** (abuse/load)
* **high denials** (security spikes)

---

## 4) What to do when an alarm fires

1. **Check recent changes**

* Last commit/tag deployed (did anything just change?)

2. **Inspect CloudWatch logs**

* Filter for:

  * `event="access_denied"` (security)
  * 5xx stack traces (availability)
* Use `request_id` to correlate a request → decision → outcome.

3. **If it’s a regression**

* Redeploy a known-good tag/commit.
* Re-run:

```bash
make smoke-dev-jwt
```

4. **If it’s load/abuse**

* Confirm throttling metrics/alarm.
* Reduce traffic / verify caller behavior.
* Keep the system safe; the demo priority is correctness + evidence.

---

## 5) Emergency procedures (“Break Glass”)

If Cognito / API Gateway is unavailable, **do not add an application backdoor endpoint**.

Use AWS IAM access to the data layer directly (DynamoDB), relying on **CloudTrail** for audit.

### Example: force-delete a corrupted document

> Illustrative: the exact keys depend on your schema.

```bash
aws dynamodb delete-item \
  --table-name ai-security-gateway-dev-docs \
  --key '{"pk": {"S": "TENANT#A"}, "sk": {"S": "DOC#123"}}'
```

### Guardrails

* Use a dedicated admin role (MFA preferred).
* Document **why** and **what** was done (ticket/notes).
* Prefer the smallest possible change (single item operations over scans/exports).
