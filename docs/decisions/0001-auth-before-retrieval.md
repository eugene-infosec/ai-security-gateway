# ADR 0001: Authorization Before Retrieval

> Truth scope: accurate as of **v1.0.0**.

## Context

Many retrieval (RAG / “chat over docs”) implementations follow a **fetch-then-filter** pattern:

1) retrieve top-*k* documents based on semantic similarity or keyword match
2) filter out any results the user should not see

**Risk:** This creates a “silent leakage” window where unauthorized text is fetched into application memory and can enter:
- snippet generation
- logs/telemetry
- LLM context windows
- downstream caches or traces

Even if post-filtering exists, bugs, partial filtering, or accidental bypass can expose sensitive content. In regulated environments, this is both a security failure and an auditability failure.

## Decision

Enforce **Auth-Before-Retrieval** as a **non-negotiable invariant**.

The gateway:
1. Derives a `Principal` (`user_id`, `tenant_id`, `role`) from trusted identity signals (deterministic headers in local demo; verified JWT claims in cloud).
2. Computes an **allowed retrieval scope** *before any store access*, expressed as:
   - `tenant_id` (structural isolation)
   - an allowed `classification` set (role/classification policy)
3. Performs retrieval only on the already-authorized scope:
   - `candidates = STORE.list_scoped(tenant_id=..., allowed_classifications=...)`
4. Runs ranking and snippet generation only on `candidates`.

This ensures the system never “touches” unauthorized content in the retrieval/snippet path.

## Consequences

### Positive

- **Stronger boundary:** Unauthorized data is never fetched into the retrieval/snippet path.
- **Audit-friendly:** Decisions are explicit and correlatable (deny receipts with `request_id` + `reason_code`).
- **Regression resistant:** The invariant is executable and continuously verified (e.g., `make verify` / `make gate`).
- **Predictable performance:** No wasted reads of data that would be discarded after the fact.

### Negative / Tradeoffs

- Authorization rules must be expressible as **scope constraints** (tenant + classification) that can be enforced structurally.
- More complex policy models (e.g., high-cardinality ABAC over many attributes) may require:
  - additional indexing / query planning
  - a more expressive policy engine
  - or precomputed access partitions
  to preserve Auth-Before-Retrieval at scale.

## Notes

This ADR intentionally prioritizes **security and reviewability** over convenience. In a regulated environment, “we fetched it but filtered it out later” is a weak guarantee-especially when snippets, logs, and traces exist.
