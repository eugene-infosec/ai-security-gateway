# Tradeoffs (Demo vs Production)
> Truth scope: accurate as of **v0.5.0**.

This document records “why” decisions so the system is believable and reviewable.

---

## Decision 1 - Identity: headers locally, JWT in cloud (defense-in-depth)

- **Decision:** Use header identity locally for deterministic tests/demos; enforce JWT at the edge in AWS.
- **Why:** Determinism locally (fast iteration, security gates), real cryptographic verification in cloud.
- **Tradeoff:** Two identity paths exist; mitigated by mapping both into the same `Principal` model and enforcing invariants after derivation.

## Decision 2 - Authorization before retrieval/snippet (non-negotiable invariant)

- **Decision:** Apply tenant + role/classification scope **before** retrieval and before snippet generation.
- **Why:** “Filter later” is audit-hostile; once unauthorized text enters the context window, it can leak.
- **Tradeoff:** Slightly more engineering upfront; far less risk and easier audits.

---

## Storage

- **Local:** in-memory tenant-scoped store for deterministic gates.
- **Cloud dev:** DynamoDB for persistence and production-shaped behavior.
- **Tradeoff:** In-memory isn’t multi-instance correct; acceptable for local proof harness.

## Retrieval

- **Current:** simple keyword scoring (demo-friendly, deterministic).
- **Tradeoff:** not a full vector DB, but still exercises the security boundary (which is the point).
- **Production direction:** vector retrieval can be added without changing invariants.

## Logging & observability

- **Decision:** structured JSON logs with a strict “safe logging” allowlist.
- **Why:** debugging is less convenient, but accidental leakage is far worse.
- **Cloud:** metric filters + alarms for denials/5xx/throttles.

## Snippet redaction

- **Decision:** redact secret-shaped strings in snippets to prevent accidental egress.
- **Why:** even authorized retrieval can leak operational secrets; snippets are an egress channel.
- **Tradeoff:** regex redaction can have false positives/negatives; acceptable for demo, and a clear seam for future DLP integration.
