# Public Sector / Healthcare Context (BC/Canada)

> Truth scope: accurate as of **v1.0.0**.

**Non-legal note:** This project demonstrates technical controls that can support privacy and security programs. It does **not** provide legal advice and does **not** claim certification or statutory compliance.

This document exists to help reviewers understand the **regulated-environment framing** for the controls demonstrated in this repo: need-to-know access, auditability, safe telemetry, and deployment-aware residency posture.

---

## Privacy contexts referenced (awareness-level)

- **FOIPPA (BC)** - *Freedom of Information and Protection of Privacy Act*
  Applies to BC public bodies (e.g., health authorities, Crown corporations, ministries).
  **Relevance:** Emphasizes protection of personal information, controlled disclosure, and auditability expectations that typically translate into **identity-first access controls** and **reviewable access decisions**.

- **PIPA (BC)** / **PIPEDA (Canada)** - private-sector privacy contexts
  Often relevant to vendors and service providers.
  **Relevance:** Common expectations include safeguarding, data minimization, and accountability (which frequently implies structured logging and evidence of controls).

---

## Clarification on data residency (BC context)

- **Status:** Historic “Canada-only” residency provisions (former s. 30.1 of FOIPPA) were **removed** in later amendments. Residency is now primarily managed via a mix of **policy**, **risk assessment**, **PIA/contractual requirements**, and **deployment controls**.

- **This architecture:** Treats residency as a **deployment property**. In a real deployment, residency posture is achieved through:
  - Region pinning (e.g., Canada regions)
  - Restricting egress (private endpoints, firewall policies, routing controls)
  - Ensuring logs/telemetry are stored in-region (log destination controls)

> **Key point:** The gateway enforces “who can access what” and “what leaves the trust boundary,” while residency is ensured by where and how you deploy supporting infrastructure.

---

## What this demo demonstrates (technical controls)

1) **Identity-first scope (need-to-know before retrieval)**
   The gateway derives `Principal` (`user_id`, `tenant_id`, `role`) server-side and enforces scope **before** any store access.

2) **Audit-grade deny receipts (forensics-ready decisions)**
   Denials emit structured events with a correlation ID (`request_id`) and a `reason_code` so investigators can reconstruct “what happened” without logging sensitive content.

3) **Tamper-evident logging posture (parsable + safe-by-default)**
   Logs are structured JSON and designed to avoid sensitive disclosure:
   - no request bodies
   - no raw query text
   - no auth headers/cookies/tokens
   Correlation is supported through `request_id` and privacy-preserving telemetry (hashes/lengths).

4) **Egress protection for snippets (DLP-shaped control)**
   Snippet output is treated as a controlled egress channel and redacted for secret-shaped strings before leaving the trusted boundary.

---

## Explicitly out of scope (by design)

This repo is **not** a complete privacy program or compliance implementation. It does not include:

- PIAs/DPIAs, policy workflows, breach procedures, or training
- Full retention / legal holds
- Formal certification claims or “compliance guarantees”
- Production network topology (private subnets, private endpoints, service mesh), beyond documented guidance

The intent is to provide a **credible, production-shaped reference implementation** that demonstrates how regulated systems are typically reviewed: controls → implementation → verifiable evidence.
