# Security Policy

This repository is a **security reference implementation**. It demonstrates technical controls (identity-first scope, fail-closed behavior, safe telemetry) and provides executable gates to prevent regressions.

---

## Reporting a Vulnerability

**Do not open a public issue.**

If you discover a potential security vulnerability in this project, please report it via one of the following channels:

- **Email:** eugene.infosec@gmail.com
- **GitHub Security Advisories:** use the repository’s “Report a vulnerability” workflow (preferred)

When reporting, please include:
- a clear description of the issue and impact
- steps to reproduce (PoC if possible)
- affected paths/versions (commit hash or release tag)
- any relevant logs/screenshots (avoid sharing secrets)

---

## Security invariants

The following invariants are enforced by code and continuously verified via `make gate` (and `make verify`):

1. **Auth-Before-Retrieval**
   Authorization and scope calculation occur **before** any retrieval/search or snippet generation.

2. **No admin leakage**
   Non-admin roles must never retrieve admin-classified titles/snippets/bodies.

3. **Strict tenant isolation**
   Data access is scoped to the authenticated tenant; cross-tenant retrieval must not be possible.

4. **Safe logging**
   Logs must never contain raw request bodies, raw query text, authorization headers/cookies/tokens, or secrets.

5. **Audit-grade deny receipts**
   Every deny path produces a structured, parsable receipt including `reason_code` and `request_id` for correlation and forensics.

6. **Snippet egress protection**
   Snippet output is redacted to reduce accidental secret leakage.

7. **Supply chain checks**
   Runtime dependencies are audited for known CVEs during gate runs.

---

## Audit log integrity

This system is designed to produce **tamper-evident, audit-friendly logs** for security-relevant events (e.g., access denied, identity resolved, schema/policy violations).

- **Log level:** security events are logged at `INFO` or `WARNING`.
- **Structure:** JSON-structured logs are designed for SIEM parsing (e.g., Splunk, Microsoft Sentinel).
- **Correlation:** all security events include a `request_id` (trace ID) to reconstruct event sequences during investigation.
- **Schema:** audit events include a `schema_version` field to support stable parsing over time.

> Note: “Immutable logs” are a deployment property (retention, access controls, write-once destinations). This repo demonstrates structured, correlation-friendly events that support those programs.
