# Architecture
> Truth scope: accurate as of **v0.5.0**.

## Goal
A multi-tenant gateway that enables “AI-style retrieval” while enforcing non-negotiable security invariants **inside** a strict trust boundary.

This project targets the most common RAG failure mode: **unauthorized retrieval** (admin leakage or cross-tenant leakage). The key idea is simple:

> If unauthorized text ever enters retrieval/snippet generation, you can’t “unfetch” it.
> So authorization must happen **before** retrieval and before any snippet is produced.

---

## High-level data flow & trust boundary

```mermaid
flowchart LR
  User["Client / User"] -->|HTTP Request| Edge["API Gateway (Edge)"]
  Edge -->|Forward Request| App["AI Security Gateway (FastAPI on Lambda)"]

  subgraph TC["Trusted Compute (Invariant Boundary)"]
    App -->|"1. Derive Principal"| Principal["Principal Resolver"]
    App -->|"2. Authorize Scope"| Policy["Policy Engine"]
    App -->|"3. Tenant-Scoped Access"| Store[("Doc Store: DynamoDB / In-Memory (local)")]
    App -->|"4. Rank + Safe Snippet"| Search["Search + Snippet Engine"]
    App -->|"5. Deny Receipt + Audit"| Audit["Safe Logger / Audit"]
  end

  Audit --> Logs[("CloudWatch / Stdout")]
```

---

## Trust model

### What is attacker-controlled (untrusted)

* Request headers and body
* Query text
* Stored document text
* Any client-supplied claims

### What is trusted (invariant boundary)

* Principal derivation
* Policy evaluation
* Tenant scoping
* Snippet redaction
* Audit logging (deny receipts)

---

## Identity source (local vs cloud)

* **Local dev:** identity is mocked via headers (`X-User`, `X-Tenant`, `X-Role`) for deterministic demos and security gates.
* **Cloud dev:** identity is enforced at the edge by an **API Gateway JWT authorizer** backed by **Cognito**. Lambda only processes requests with valid, cryptographically signed claims, which are mapped into the same `Principal` model used locally.

---

## Security invariants (enforced by code + checked by `make gate`)

1. **Auth-Before-Retrieval:** permissions are applied to the retrieval scope (not filtered post-fetch).
2. **Strict Tenant Isolation:** tenant is derived server-side; storage reads/writes are tenant-scoped.
3. **No Admin Leakage:** non-admin roles must never retrieve admin-classified titles/snippets.
4. **Safe Logging:** logs must never contain raw request bodies/queries/auth headers.
5. **Evidence-over-Claims:** denials are traceable via `request_id` and backed by numbered evidence artifacts.
6. **No Secret Egress via Snippets:** snippet output is redacted to prevent leaking secrets even if they exist in stored docs.

---

## Request flows

### Local request flow (deterministic)

* Identity is provided via headers: `X-User`, `X-Tenant`, `X-Role`.
* Middleware assigns a `request_id` and returns `X-Request-Id`.
* Authorization is evaluated before sensitive actions:

  * before ingestion writes
  * before query retrieval/snippet generation
* Storage access is tenant-scoped (structural isolation).
* Logging is structured JSON (“deny receipts”).

### Cloud dev slice (AWS)

Provisioned via Terraform:

* Lambda (Python 3.12)
* API Gateway HTTP API
* Cognito user pool + client for JWT issuance
* CloudWatch log retention (7 days)
* CloudWatch alarms: 5xx errors, throttles, high denials
* Metric filter counts deny receipts from structured logs

---

## Proof hooks

* `make gate` runs:

  * `no_admin_leakage_gate`
  * `tenant_isolation_gate`
  * `safe_logging_gate`

Evidence is indexed in `evidence/INDEX.md`.

> If you only review one thing: the claims are executable (`make ci` / `make gate`) and supported by screenshots in `evidence/`.
