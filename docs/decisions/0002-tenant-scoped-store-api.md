# 0002 — Tenant-scoped Store API

## Decision
All store operations are tenant-scoped by construction. There is no "list all docs" API.

## Why
- Prevents cross-tenant bugs by making unsafe access patterns impossible.
- Makes auth-before-retrieval simpler: the query engine can only ever see docs from a single tenant.

## Consequences
- Query paths must always supply tenant_id from the authenticated principal (authority derivation).