````markdown
# System Architecture & Trust Boundaries

This gateway prevents the most common RAG failure mode: **unauthorized retrieval** (admin leakage or cross-tenant leakage) by enforcing **auth-before-retrieval** inside a strict trust boundary.

## High-Level Data Flow

```mermaid
graph LR
    User[Client / User] -->|HTTP Request| Edge[Edge / API Gateway]
    Edge -->|Forward Request| App[AI Security Gateway (FastAPI on Lambda)]

    subgraph "Trusted Compute (Invariant Boundary)"
        App -->|1. Derive Principal| Principal[Principal Resolver]
        App -->|2. Authorize Scope| Policy[Policy Engine]
        App -->|3. Tenant-Scoped Access| Store[(Doc Store: DynamoDB / Memory)]
        App -->|4. Rank + Safe Snippet| Search[Search + Snippet Engine]
        App -->|5. Deny Receipt + Audit| Audit[Safe Logger / Audit]
    end

    Audit --> Logs[(CloudWatch / Stdout)]
````

## Trust Model (What is trusted vs. attacker-controlled)

* **Untrusted inputs:** request headers/body, queries, document text, any client-supplied claims.
* **Trusted boundary:** principal derivation, policy evaluation, tenant scoping, snippet redaction, audit logging.

* **Identity Source:** In Local Dev, identity is mocked via headers (X-User) for speed. In AWS, identity is enforced by Cognito + API Gateway JWT Authorizer. The Lambda function only processes requests with valid, cryptographically signed claims.

## Security Invariants (Enforced by construction)

1. **Auth-Before-Retrieval:** permissions are applied to the retrieval scope (not filtered after fetching).
2. **Strict Tenant Isolation:** tenant is derived server-side; storage reads are tenant-scoped.
3. **No Admin Leakage:** interns can never retrieve admin-classified titles/snippets.
4. **Evidence-Over-Claims:** every deny emits a structured audit event with `request_id` + `reason_code`.

## Proof Mapping (Where to verify)

* `make gate` runs the misuse regression suite:

  * no admin leakage
  * tenant isolation
  * safe logging contract
* Deny receipts are emitted as `event=access_denied` and can be observed in logs (see `evidence/`).

```
