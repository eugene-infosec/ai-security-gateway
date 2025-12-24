# Tradeoffs

> Truth scope: accurate as of **v0.7.0**.
> Scope: this is a **production-shaped demo** optimized for security invariants, auditability, and interview clarity—not maximum feature surface.

This document captures “why” decisions so the system is believable, reviewable, and easy to defend in interviews.

---

## Decision 1 - Identity: headers locally, JWT at the edge in cloud (defense-in-depth)

* **Decision:**

  * **Local dev:** deterministic header identity (`X-User`, `X-Tenant`, `X-Role`) for fast iteration and repeatable tests.
  * **Cloud dev:** enforce JWT at the edge using **API Gateway JWT authorizer + Cognito**, and derive `Principal` from verified claims.

* **Why:**

  * Local determinism makes the **security gates** reliable and fast.
  * Cloud JWT enforcement ensures real cryptographic verification and prevents spoofing before Lambda runs.

* **Tradeoff:** two identity paths exist.
  **Mitigation:** both paths map into the same `Principal` model, and all security invariants are enforced *after* principal derivation inside the trusted compute boundary.

---

## Decision 2 - Authorization before retrieval and before snippet generation (non-negotiable)

* **Decision:** apply tenant scope + role/classification rules **before** any store reads that could return unauthorized content, and **before** snippet generation.

* **Why:** “retrieve then filter” is audit-hostile: once unauthorized text enters memory or a context window, you can’t reliably undo exposure.

* **Tradeoff:** slightly more engineering upfront and more discipline in data access patterns.
  **Payoff:** simpler audits, stronger guarantees, and fewer catastrophic failure modes.

---
## Storage

* **Decision:** In-Memory, tenant-scoped store for both Local and Cloud environments.
* **Why:**
  1. **Zero Cost:** No idle DynamoDB costs for the demo.
  2. **Simplicity:** Removes IAM/Table provisioning complexity for reviewers running the demo.
* **Tradeoff:** Data is lost when the Lambda cold starts or container restarts.
* **Mitigation:** The architecture enforces scoping *logically* in the code (`app/store.py`), so the security invariant (Tenant Isolation) is proven regardless of the backing engine.

---

## Retrieval

* **Current:** simple keyword scoring (deterministic, demo-friendly).
* **Why:** the thesis is the **security boundary** (auth-before-retrieval + isolation + audit), not embeddings or ranking quality.

**Tradeoff:** not a full vector database and not representative of production retrieval quality.
**Production direction:** vector retrieval can be added later without changing the invariants, because authorization still constrains scope before retrieval.

---

## Logging and observability

* **Decision:** structured JSON logs with a strict safe-logging allowlist; no request bodies, query text, or auth material.
* **Why:** accidental leakage into logs is a common real-world incident class, and logs are frequently exported broadly.

**Tradeoff:** debugging is less convenient.
**Mitigation:** correlation via `request_id`, explicit deny receipts, and targeted CloudWatch alarms (5xx / throttles / high denials).

---

## Snippet redaction

* **Decision:** redact secret-shaped strings in snippets to prevent accidental egress from stored content.
* **Why:** snippet output is an egress channel; even authorized retrieval can unintentionally expose operational secrets.

**Tradeoff:** regex redaction can have false positives and false negatives.
**Why acceptable:** it’s a pragmatic safety net for v0.7.0 and a clear seam for future DLP-style controls (better detectors, allowlists, tenant-specific policies).
