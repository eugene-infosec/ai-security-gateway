# Tradeoffs

> Truth scope: accurate as of **v1.0.0**.
> Demo scope: this is a **production-shaped reference implementation** optimized for **security invariants**, **auditability**, and **reviewer clarity** - not maximum feature surface.

This document captures “why” decisions so the system is believable, reviewable, and easy to defend in interviews and regulated-environment reviews.

---

## Decision 1 - Identity: Headers locally, JWT at the edge in cloud (defense-in-depth)

**Decision**
- **Local dev:** deterministic header identity (`X-User`, `X-Tenant`, `X-Role`) for fast iteration and repeatable tests.
- **Cloud dev:** enforce JWT at the edge using **API Gateway JWT authorizer + Cognito**, and derive `Principal` from verified claims.

**Why**
- Local determinism makes the **security gates** reliable and fast (no network calls to an IdP).
- Cloud JWT enforcement ensures real cryptographic verification and prevents spoofing before Lambda runs.

**Tradeoff**
- Two identity paths exist.

**Mitigation**
- Both paths map into the same `Principal` model, and all security invariants are enforced **after principal derivation** inside the trusted compute boundary.

---

## Decision 2 - Authorization before retrieval and before snippet generation (non-negotiable)

**Decision**
- Apply tenant scope + role/classification rules **before** any store reads that could return unauthorized content, and **before** snippet generation.

**Why**
- “Retrieve then filter” is audit-hostile: once unauthorized text enters memory (or a context window), you can’t reliably undo exposure.

**Tradeoff**
- Slightly more engineering upfront and more discipline in data access patterns.

**Payoff**
- Stronger guarantees, simpler audits, and fewer catastrophic failure modes.

---

## Decision 3 - Storage: Ephemeral in-memory store (demo reproducibility over durability)

**Decision**
- Use a strictly scoped `InMemoryStore` for both Local and Cloud demo environments.

**Why**
1. **Reproducibility:** a reviewer can `make run-local` and get a working system immediately without Docker or cloud credentials.
2. **Cost safety:** eliminates idle database cost in the cloud demo slice.
3. **Clarity:** keeps the review focused on the **gateway controls**, not data infrastructure.

**Tradeoff**
- Data is lost when the process stops (local) or a Lambda cold-start resets state (cloud).

**Mitigation**
- Scoping is enforced logically via the `Store` interface (`list_scoped`, `put`). Swapping to a persistent store in production (DynamoDB / pgvector / managed vector DB) preserves invariants because scope is still applied **before retrieval**.

---

## Decision 4 - Retrieval: Deterministic lexical search vs. vector search

**Decision**
- Use deterministic lexical matching / keyword scoring for retrieval.

**Why**
- The thesis is the **security boundary** (identity-first scope + isolation + audit receipts), not ranking quality.
- Deterministic retrieval makes verification gates and evidence repeatable.

**Tradeoff**
- Not representative of production retrieval quality.

**Production direction**
- Vector retrieval can be added later without changing the invariants, because authorization still constrains scope **before** any retrieval operation and before snippets are emitted.

---

## Decision 5 - Logging & observability: Safe-by-default telemetry contract

**Decision**
- Structured JSON logs with a strict global safe logging filter and explicit “red lines”:
  - never log request bodies
  - never log raw query text
  - never log auth headers/cookies/tokens

**Why**
- Accidental leakage into logs is a common real-world incident class, and logs are often exported broadly (SIEM, analytics, vendors).

**Tradeoff**
- Debugging is less convenient (you can’t see raw payloads).

**Mitigation**
- Correlation via `request_id` (aliased as `X-Trace-Id`), explicit deny receipts with `reason_code`, and correlation-safe query telemetry (`query_sha256`, `query_len`).

---

## Decision 6 - Deny receipts: “audit-ready” instead of “immutable”

**Decision**
- Emit structured deny receipts on every blocked action with:
  - `event="access_denied"`
  - `reason_code`
  - `request_id`
  - principal context fields (when known)

**Why**
- In regulated environments, the ability to answer “who tried what, when, and why was it denied?” matters as much as prevention.

**Tradeoff**
- Receipts must be designed to avoid sensitive disclosure while still being useful.

**Mitigation**
- Deny receipts include **correlation** and **decision metadata**, not raw content. Log safety rules prevent tokens/bodies/queries.

---

## Decision 7 - Snippet redaction: Regex-based DLP seam vs. ML-based detectors

**Decision**
- Redact secret-shaped strings in snippets using fast regex patterns.

**Why**
- Snippet output is an egress channel; even authorized retrieval can unintentionally expose operational secrets embedded in valid documents.
- Regex is deterministic, low-latency, and easy to reason about.

**Tradeoff**
- Regex is imperfect (false positives/negatives).

**Why acceptable**
- It’s a pragmatic safety net for v1.0.0 and establishes a clear seam for stronger DLP controls later (allowlists, tenant policies, external scanners, classifiers).

---

## Decision 8 - Build strategy: Native wheel vendoring vs. Docker builds

**Decision**
- Use a custom packaging script (`scripts/package_lambda.py`) to vendor `manylinux2014_x86_64` wheels rather than building inside Docker.

**Why**
- Reviewer friction. Requiring Docker blocks many reviewers (especially on Mac/Windows) from deploying the cloud slice quickly.

**Tradeoff**
- We assume the complexity of managing a packaging script instead of relying on a containerized build environment.

**Mitigation**
- Lambda architecture is pinned (e.g., `x86_64`) to match vendored wheel compatibility, and the build is reproducible via Make targets.

---

## Decision 9 - “Compliance-aligned” language: truth-scoped posture

**Decision**
- Use “privacy-aligned controls” / “audit-ready evidence” language and avoid “certified compliant” claims.

**Why**
- Compliance is a program (people/process/policy), not a repo. Over-claiming is a hiring red flag in regulated environments.

**Tradeoff**
- Less marketing hype.

**Payoff**
- Credibility with security, privacy, and public sector reviewers: controls are demonstrable, evidence-backed, and scoped honestly.
