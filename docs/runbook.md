# Operational Runbook (Dev)

> Truth scope: accurate as of **v0.9.2**.

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
curl -s [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
curl -s [http://127.0.0.1:8000/whoami](http://127.0.0.1:8000/whoami) \
  -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'

```

### Verification (Client & Invariants)

**1. Client Contract (90-Second Verify):**

```bash
python examples/reference-client/verify.py

```

**2. Deep Security Gates:**

```bash
make ci
# or:
make gate

```

### Required before commit

```bash
make review

```

---

## 2) Cloud dev workflow (AWS)

### Verify AWS identity

```bash
make doctor-aws

```

### Deploy

**Note:** This command now automatically builds the Lambda artifact (using the native wheel vendor script) before deploying. Docker is not required.

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
* **SafeLogFilter:** Enforced globally. **Never** log request bodies, query text, auth headers, or tokens.
* Use `request_id` (aliased as **`trace_id`** or `X-Trace-Id`) for correlation.


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
make smoke-cloud

```


4. **If it’s load/abuse**
* Confirm throttling metrics/alarm.
* Reduce traffic / verify caller behavior.
* Keep the system safe; the demo priority is correctness + evidence.

---

## 5) Emergency procedures / State Reset

### Demo Environment (v0.9.0+)

Since **v0.9.0** uses **ephemeral in-memory storage** to ensure reproducibility and zero cost, there is no persistent database to patch manually.

**To clear corrupted state:**

```bash
# Force a full infrastructure cycle
make destroy-dev
make deploy-dev

```

### Production Scenario (Reference)

In a real deployment using a persistent store (e.g., DynamoDB or Vector DB):

1. Use a dedicated admin IAM role (MFA preferred).
2. Access the store directly via AWS CLI or Console to repair records.
3. **CloudTrail** provides the audit trail for these manual interventions.
