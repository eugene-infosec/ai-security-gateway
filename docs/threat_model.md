# Threat Model

> Truth scope: accurate as of **v1.0.0**.

This document focuses on the project’s core security goal: **prevent unauthorized retrieval** (cross-tenant leakage and role/classification leakage) and provide **audit-ready evidence** when the gateway blocks an action.

This is a reference implementation demonstrating technical controls and evidence generation. It does **not** claim compliance certification.

---

## 1) Assets

- **Tenant documents:** titles, snippets, bodies
- **Admin-classified documents:** higher sensitivity content that must never be exposed to non-admin roles
- **Identity context:** `Principal` (`user_id`, `tenant_id`, `role`)
- **Audit logs + metrics:** must not leak request contents, secrets, or tokens; must be correlation-friendly
- **Snippet output:** an egress channel that must not leak secret-shaped strings

---

## 2) Trust boundaries

1. **Client → Gateway:** untrusted input (requests are attacker-controlled)
2. **Gateway policy engine:** trusted enforcement point (security decisions happen here)
3. **Store:** passive; the gateway must enforce scoping and authorization (no “DB does RBAC” assumption)
4. **Logs/metrics:** must be safe, parsable, and correlation-friendly
5. **Snippet/redaction layer:** must reduce risk of “secret egress” from stored content

---

## 3) Threats, mitigations, and proof

### T0: Identity attribute tampering (privilege escalation)

**Threat:** A malicious user attempts to overwrite their own `role` or `tenant_id` attributes in the Identity Provider to gain admin privileges or access another tenant's data.

**Mitigation:**
- **Edge-validated identity:** In cloud mode, API Gateway validates JWTs issued by Cognito; the gateway derives identity from verified claims (no client-side assertions).
- **Fail-closed identity resolution:** Requests without valid identity are rejected; unknown roles fail closed with a deny receipt.

**Proof:**
- `/whoami` derives the principal from verified JWT claims (cloud) or deterministic headers (local).
- Unknown roles produce `ROLE_UNKNOWN_FAIL_CLOSED` deny receipts (policy layer).

---

### T1: Cross-tenant data leakage (BOLA)

**Threat:** Tenant A attempts to retrieve Tenant B content (intentionally or via bug).

**Mitigation:**
- Tenant is derived **server-side** (local header mode for deterministic demos; verified JWT claims in cloud).
- All storage reads/writes are **tenant-scoped by construction** via `STORE.list_scoped(tenant_id=...)` and `STORE.put(tenant_id=...)`.

**Proof:**
- `evals/tenant_isolation_gate.py`

---

### T2: Admin data leakage to non-admin roles (IDOR / privilege bypass)

**Threat:** Non-admin roles retrieve admin-classified titles/snippets/bodies.

**Mitigation:**
- Role/classification authorization is enforced **before retrieval** and **before snippet generation**.
- Classification constraints are applied to the retrieval scope (not “filter after fetch”).

**Proof:**
- `evals/no_admin_leakage_gate.py`

---

### T3: Sensitive data leakage via logs (telemetry exfiltration)

**Threat:** Request bodies, raw query text, auth headers/cookies/tokens, or secret-shaped strings leak into logs (accidentally or via debug code).

**Mitigation:**
- **Global safe logging controls:** A `SafeLogFilter` (and/or audit payload validation) prevents unsafe keys/values from being logged.
- Structured JSON logs designed to be SIEM-parsable.
- For correlation without disclosure, query telemetry uses **hashes and lengths** (e.g., `query_sha256`, `query_len`) instead of raw query text.

**Proof:**
- `evals/safe_logging_gate.py`

---

### T4: Secret leakage via snippets (content egress)

**Threat:** Even when access is authorized, snippet output could leak secret-shaped strings (e.g., API keys) present in stored docs.

**Mitigation:**
- Regex-based snippet redaction on `/query` output to scrub secret-shaped patterns before egress.

**Proof:**
- Evidence artifact `E08_redaction_proof.png` (see `evidence/INDEX.md`)

---

### T5: Abuse / DoS / unexpected load (cloud)

**Threat:** Traffic spikes (malicious or accidental) degrade availability or inflate cost.

**Mitigation:**
- API Gateway throttling at the edge.
- CloudWatch alarms for 5xx, throttles, and high denials.
- Fast teardown kill switch for dev: `make destroy-dev`.

**Proof:**
- Terraform infra + evidence artifacts for alarms and smoke tests (see `evidence/INDEX.md`)

---

### T6: Supply chain, deployment integrity & misconfiguration

**Threat:** Vulnerable dependencies, configuration drift, or incompatible binary artifacts weaken invariants or cause availability failures.

**Mitigation:**
- **Dependency scanning:** `pip-audit` runs in gates/CI to surface known CVEs.
- **Artifact integrity:** Packaging script vendors compatible wheels for Lambda targets to avoid host pollution and binary mismatch.
- **Fail-closed startup checks:** Invalid auth mode or unsafe header-mode configuration halts startup.

**Proof:**
- `make gate` / `make verify` includes `pip-audit`
- `scripts/package_lambda.py`
- Startup checks in `app/main.py`

---

## 4) Prevention of bypass (production architecture)

> **Note:** This section documents how a production deployment would prevent direct access to the data layer, bypassing the gateway. These controls are intentionally **not implemented** in this demo to reduce friction - but are called out here to demonstrate production awareness.

### Why this matters

The gateway enforces authorization **only if** traffic flows through it. In a naïve deployment, an attacker (or misconfigured service) could query the backing store directly, bypassing all policy enforcement.

### Production mitigations

| Attack vector | Mitigation | Implementation notes |
|---|---|---|
| **Direct store access** | Private network isolation | Place data plane in private subnets; only gateway runtime can reach it. |
| **Stolen runtime credentials** | IAM least privilege + VPC endpoints | Scope runtime role to only required resources; reduce exfil paths. |
| **Rogue internal service** | Service identity + mTLS | Enforce mutual TLS or workload identity between services. |
| **Misconfigured edge** | API Gateway policies | Restrict invoke permissions; limit exposure of internal routes. |
| **Log/metric exfiltration** | Encryption + resource policies | Encrypt logs; explicitly control cross-account access. |

### Why not implemented here

1. **Reviewer friction:** VPCs/NAT/private subnets complicate `make deploy-dev` and increase cost.
2. **Orthogonal to thesis:** The core thesis is **Auth-Before-Retrieval invariants**, not network topology.
3. **Demo ROI:** Hiring reviewers can verify security logic in minutes; verifying VPC topology requires console access and adds little signal.

> **TL;DR:** This demo proves retrieval authorization and auditability; production network hardening is acknowledged and documented, but intentionally not required for the core hiring signal.

---

## 5) Residual risks and next steps (explicitly out of scope for v1.0.0)

- WAF + more nuanced rate limiting (per principal / per tenant)
- Per-tenant encryption strategies (e.g., CMKs, envelope encryption)
- Distributed tracing + SLIs/SLOs beyond alarms and structured logs
- More comprehensive DLP (beyond regex redaction; e.g., classification-aware policies or external scanners)
- Formal privacy program artifacts (PIA/DPIA workflows, breach procedures, retention/legal holds)
