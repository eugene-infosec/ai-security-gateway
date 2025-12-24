# ADR 0001: Authorization Before Retrieval

> Truth scope: accurate as of **v0.8.0**.

## Context

Many RAG implementations follow a **fetch-then-filter** pattern: retrieve top-*k* documents, then remove any results the user should not see.

**Risk:** this creates a “silent leakage” window where unauthorized text is fetched into application memory (and can enter snippet generation / context windows). If filtering is buggy, incomplete, or bypassed, sensitive content can leak.

## Decision

Enforce **Auth-Before-Retrieval** as a non-negotiable invariant.

The gateway derives a `Principal` (user, tenant, role) and uses the `PolicyEngine` to compute an **allowed retrieval scope** (e.g., `tenant_id` + allowed `classification` set) **before** constructing any storage query or retrieval candidate set.

Storage reads are tenant-scoped by design (structural isolation), and retrieval/snippet generation runs only on the already-authorized candidate set.

## Consequences

### Positive

* Unauthorized data is never fetched into the retrieval/snippet path (stronger security boundary).
* Security properties are testable and regression-resistant (`make gate` asserts the invariant).
* More predictable performance: no wasted reads of data that would be discarded later.

### Negative

* Authorization rules must be expressible as **scope constraints** (tenant/classification) that can be enforced structurally.
* Some advanced policy models (e.g., per-row ABAC with many attributes) may require additional indexing or a more expressive authorization layer to preserve auth-before-retrieval at scale.
