# Demo Script (2–5 minutes)
> Truth scope: accurate as of **v0.3.0**

## 1) Prove the invariants (local)
Run the invariant harness:

```bash
make gate
```

**Show the PASS lines:**

   * no admin leakage

   * tenant isolation

   * safe logging

## 2) Show a deny receipt (local)

```Bash
make run-local
```
In another terminal:
```Bash
curl -i -X POST [http://127.0.0.1:8000/ingest](http://127.0.0.1:8000/ingest) \
  -H 'Content-Type: application/json' \
  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
  -d '{"title":"HACK","body":"x","classification":"admin"}'
```
Point to evidence/INDEX.md (E01).

## 3) Cloud dev slice (AWS)

```Bash
make doctor-aws
make deploy-dev
make smoke-dev
make logs-cloud
make destroy-dev
```

Point to evidence/INDEX.md (E03–E05).

## Planned next (Phase 6)

    JWT authorizer at API Gateway

    /whoami proves principal derived from JWT claims
