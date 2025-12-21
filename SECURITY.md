# Security Policy

## Reporting a Vulnerability

**Do not open a public issue.**

If you discover a potential security vulnerability in this project, please report it via email or GitHub Security Advisories.

## Security Invariants

This project is a security reference implementation. The following invariants are strictly enforced via `make gate`:

1.  **No Admin Leakage**: Non-admin roles cannot access admin data.
2.  **Tenant Isolation**: Data access is scoped to the authenticated tenant.
3.  **Safe Logging**: No raw secrets or bodies in logs.
