# Retrospective (v0.8.0) - The Golden Build

This repo is intentionally **demo-scoped** but **production-shaped**. This retrospective documents concrete issues found during the hardening phase, why they matter, and what was shipped to fix them in the v0.8.0 release.

## 1) Vulnerability Management: The "Zero Code" Fix

**Issue:** The project depended on `python-jose` to parse tokens, but that library (and its `ecdsa` dependency) had known CVEs. Patching was difficult due to slow upstream maintenance.

**Fix:** **Deleted the dependency.**
- **Cloud:** We rely on AWS API Gateway to cryptographically validate the JWT signature *before* the Lambda is invoked. The Lambda code now treats the claims in the request scope as trusted.
- **Local:** We use explicit headers (`X-User`, etc.) for deterministic testing.
- **Result:** The attack surface was eliminated by architecture, not by patching.

## 2) Identity Boundary: Privilege Escalation Prevention

**Issue:** The Terraform configuration for Cognito allowed the `custom:role` and `custom:tenant_id` attributes to be mutable and writable by the client. This theoretically allowed a compromised client to rewrite their own identity token to escalate privileges.

**Fix:**
- Attributes are now set to **`mutable = false`** in Terraform.
- The App Client is restricted from writing to these attributes.
- **Result:** Identity claims are now an immutable trust anchor rooted in the bootstrap/admin process.

## 3) Architectural Honesty: Dead Code Elimination

**Issue:** The codebase contained a `DynamoDBStore` implementation that was not used in the default configuration (which uses `InMemoryStore` for reproducibility). This "dead code" confused reviewers about the actual data path and increased the maintenance surface.

**Fix:** **Removed `DynamoDBStore` entirely.**
- The project now honestly presents itself as an in-memory reference implementation.
- The `Store` interface remains strictly defined, so a persistent backing store can be re-injected in the future without changing the security logic.

## 4) Operational Maturity: Safe Logging

**Issue:** While audit logs were structured, standard application logs (stdout) could potentially leak sensitive headers or query parameters if a developer added a careless `print()` or if a library logged verbose errors.

**Fix:**
- Implemented a global `SafeLogFilter` in `app/json_logger.py`.
- It actively scans all log records (including `extras`) for forbidden keys (e.g., `authorization`, `cookie`, `body`) and blocks them before they reach stdout.

## 5) Known limitations (intentional)

- **InMemoryStore:** It is cheap, deterministic, and perfect for demoing invariants, but it is not durable or concurrency-safe for real production use.
- **Lexical Search:** Retrieval uses deterministic keyword scoring. Vector search is a valid future enhancement, but the security invariants (Auth-Before-Retrieval) apply identically to both.
