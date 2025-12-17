# Runbook (Dev)
> Truth scope: accurate as of **v0.4.0**

## Local workflow
- Install: `make install`
- Run: `make run-local`
- Required before commit: `make preflight`
- Security regression harness: `make gate`

## Cloud dev workflow (AWS)
- Verify identity: `make doctor-aws`
- Deploy: `make deploy-dev`
- Smoke test: `make smoke-dev`
- Tail logs: `make logs-cloud`
- Kill switch (cost safety): `make destroy-dev`

## Operational notes
- If smoke fails: check CloudWatch logs first (request_id correlation).
- If throttles alarm triggers: treat as abuse/load signal.
- If high denials alarm triggers: treat as potential attack or client misbehavior.

## Cost safety
Always run `make destroy-dev` after demo/testing.
