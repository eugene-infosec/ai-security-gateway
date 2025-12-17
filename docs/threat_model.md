# Threat Model
> Truth scope: accurate as of **v0.5.0**.

## Assets

- Tenant documents (titles/snippets/bodies)
- Admin-classified documents
- Identity context (Principal: user_id, tenant_id, role)
- Logs and metrics (must not leak content/secrets)
- Snippet output (must not leak secrets)

## Trust boundaries

1) **Client → Gateway:** untrusted input
2) **Gateway policy engine:** trusted enforcement point
3) **Store:** passive; access must be scoped by the app
4) **Logs/metrics:** must be safe and non-sensitive
5) **Snippet/redaction:** must enforce “no secret egress”

## Primary threats & mitigations

### T1: Cross-tenant data leakage (BOLA)
- **Mitigation:** server-side tenant derivation + tenant-scoped storage access
- **Proof:** `tenant_isolation_gate`

### T2: Admin data leakage to non-admin roles (IDOR)
- **Mitigation:** role/classification rules enforced before retrieval/snippet
- **Proof:** `no_admin_leakage_gate`

### T3: Sensitive data leakage via logs
- **Mitigation:** safe logging allowlist; never log request bodies/queries/auth headers
- **Proof:** `safe_logging_gate`

### T4: Secret leakage via snippets (content egress)
- **Mitigation:** regex-based snippet redaction on `/query` output
- **Proof:** evidence artifact `E08_redaction_proof.png`

### T5: Abuse / DoS / unexpected load (cloud)
- **Mitigation:** throttling + alarms + fast teardown (`make destroy-dev`)
- **Proof:** numbered evidence of alarms + smoke tests

### T6: Misconfiguration drift (cloud)
- **Mitigation:** Terraform formatting/validation + repeatable Make targets

## Residual risks & next steps (explicitly out-of-scope for v0.5.0)

- Stronger key management (Secrets Manager / Parameter Store)
- WAF + more nuanced rate limiting per principal
- Per-tenant CMK / per-item envelope encryption (compliance needs)
- Distributed tracing + SLIs/SLOs (beyond CloudWatch alarms)
