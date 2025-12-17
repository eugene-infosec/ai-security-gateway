# ADR 0001: Authorization Before Retrieval

## Context
RAG systems typically use a "Fetch-then-Filter" pattern: fetch top-k documents, then filter out the ones the user isn't allowed to see.
**Risk:** This creates a "Silent Leakage" window where unauthorized data enters the application memory and context window. If the filter has a bug, data leaks.

## Decision
We enforce **Auth-Before-Retrieval**.
The `PolicyEngine` calculates the allowed scope (e.g., `tenant_id` AND `classification`) *before* the database query is constructed. The storage layer only executes queries bounded by this scope.

## Consequences
- **Positive**: Unauthorized data never leaves the database. "Admin" documents are never fetched for "Interns".
- **Positive**: Performance is predictable; we never fetch data we plan to discard.
- **Negative**: Complex permission rules must be mappable to database query keys (structural isolation).
