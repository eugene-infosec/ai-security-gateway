# Tradeoffs

> Truth scope: accurate as of **v0.9.2**.

> Demo scope: this is a **production-shaped demo** optimized for security invariants, auditability, and interview clarity - not maximum feature surface.

> This document captures “why” decisions so the system is believable, reviewable, and easy to defend in interviews.

---

## Decision 1 - Identity: Headers locally, JWT at the edge in cloud (defense-in-depth)

* **Decision:**
  * **Local dev:** deterministic header identity (`X-User`, `X-Tenant`, `X-Role`) for fast iteration and repeatable tests.
  * **Cloud dev:** enforce JWT at the edge using **API Gateway JWT authorizer + Cognito**, and derive `Principal` from verified claims.

* **Why:**
  * Local determinism makes the **security gates** reliable and fast (no network calls to IdP).
  * Cloud JWT enforcement ensures real cryptographic verification and prevents spoofing before Lambda runs.

* **Tradeoff:** Two identity paths exist.
  **Mitigation:** Both paths map into the same `Principal` model, and all security invariants are enforced *after* principal derivation inside the trusted compute boundary.

---

## Decision 2 - Authorization before retrieval and before snippet generation (non-negotiable)

* **Decision:** Apply tenant scope + role/classification rules **before** any store reads that could return unauthorized content, and **before** snippet generation.

* **Why:** “Retrieve then filter” is audit-hostile: once unauthorized text enters memory or a context window, you can’t reliably undo exposure.

* **Tradeoff:** Slightly more engineering upfront and more discipline in data access patterns.
  **Payoff:** Simpler audits, stronger guarantees, and fewer catastrophic failure modes.

---

## Decision 3 - Storage: In-Memory (Ephemeral)

* **Decision:** Use a strictly scoped `InMemoryStore` for both Local and Cloud demo environments.
* **Why:**
  1. **Reproducibility:** A reviewer can `make run-local` and get a working system immediately without Docker or AWS credentials.
  2. **Zero Cost:** Eliminates idle DynamoDB/RDS costs for the cloud demo.
  3. **Simplicity:** Focuses the code review on the *Security Gateway logic*, not database infrastructure.
* **Tradeoff:** Data is lost when the process stops (Local) or the Lambda cold-starts (Cloud).
* **Mitigation:** The architecture enforces scoping *logically* via the `Store` interface (`list_scoped`). Swapping this for a persistent `DynamoDBStore` in production is a 1-file change that does not alter the security invariants.

---

## Decision 4 - Retrieval: Lexical vs. Vector

* **Decision:** Simple keyword scoring (deterministic, demo-friendly).
* **Why:** The thesis is the **security boundary** (auth-before-retrieval + isolation + audit), not embeddings or ranking quality.

* **Tradeoff:** Not a full vector database and not representative of production retrieval quality.
* **Production direction:** Vector retrieval can be added later without changing the invariants, because authorization still constrains scope *before* retrieval.

---

## Decision 5 - Logging and Observability

* **Decision:** Structured JSON logs with a strict global `SafeLogFilter`; no request bodies, query text, or auth material allowed.
* **Why:** Accidental leakage into logs is a common real-world incident class, and logs are frequently exported broadly.

* **Tradeoff:** Debugging is less convenient (cannot see the full payload).
* **Mitigation:** Correlation via `request_id` (aliased as `trace_id` for clients), explicit deny receipts, and targeted CloudWatch alarms (5xx / throttles / high denials).

---

## Decision 6 - Snippet Redaction (Regex)

* **Decision:** Redact secret-shaped strings in snippets using high-performance Regex patterns.
* **Why:** Snippet output is an egress channel; even authorized retrieval can unintentionally expose operational secrets present in valid documents.

* **Tradeoff:** Regex redaction is imperfect (false positives/negatives).
* **Why acceptable:** It is a pragmatic safety net for v0.9.0 and establishes a clear seam for future DLP-style controls (better detectors, allowlists, tenant-specific policies).

---

## Decision 7 - Build Strategy: Native Wheel Vendoring vs. Docker

* **Decision:** Use a custom Python script (`scripts/package_lambda.py`) to download and vendor `manylinux2014_x86_64` wheels instead of building inside Docker.
* **Why:** Reviewer friction. Requiring Docker prevents many reviewers (especially on Mac/Windows) from easily deploying the cloud slice.
* **Tradeoff:** We assume the complexity of managing a build script rather than the complexity of managing a container runtime.
* **Mitigation:** We explicitly lock the Terraform Lambda architecture to `x86_64` to guarantee compatibility with the vendored wheels.
