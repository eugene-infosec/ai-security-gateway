# Threat Model
> Truth scope: accurate as of **v0.4.0**.

## Assets
- Tenant documents (titles/snippets/bodies)
- Admin-classified documents
- Identity context (Principal: user_id, tenant_id, role)
- Logs and metrics (must not leak content/secrets)

## Trust boundaries
1) Client → Gateway: untrusted input
2) Gateway policy engine: trusted enforcement point
3) Store: trusted, scoped access
4) Logs/metrics: must be safe and non-sensitive

## Primary threats & mitigations
### T1: Cross-tenant data leakage
- Mitigation: server-side tenant scoping in storage access
- Proof: `tenant_isolation_gate`

### T2: Admin data leakage to non-admin roles
- Mitigation: role-based scope (intern cannot see admin-classified docs)
- Proof: `no_admin_leakage_gate`

### T3: Sensitive data leakage via logs
- Mitigation: safe logging guardrails (no raw `body`, `query`, auth headers)
- Proof: `safe_logging_gate`

### T4: Abuse / DoS / unexpected load (cloud)
- Mitigation: CloudWatch alarms (throttles), fast teardown (`make destroy-dev`)
- Proof: numbered evidence of alarms + smoke tests

### T5: Misconfiguration drift (cloud)
- Mitigation: Terraform fmt/validate checks and repeatable Make targets

## Implemented threats (Phase 6+)
- Token spoofing / identity tampering → JWT authorizer at API Gateway (Done).
