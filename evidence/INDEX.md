# Evidence Artifact Index
> Truth scope: accurate as of **v0.5.0**.
>
> All artifacts are referenced by ID to ensure traceability.

| ID  | File                               | Claim / Proof
| :-- | :--------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| E00 | `INDEX.md`                         | Evidence map: artifact IDs → exact proof files (traceability)                             |
| E01 | `E01_attack_receipt_local.png`     | **Local** 403 produces structured deny receipt (`event=access_denied`, `reason_code`, `request_id`)               |
| E02 | `E02_gate_pass_local.png`          | **Misuse regression suite passes** (`make gate`): no-admin-leakage, tenant-isolation, safe-logging invariants  |
| E03 | `E03_smoke_dev_output.png`         | **AWS deployed** endpoint passes smoke (`make smoke-dev`): health, identity, deny path                                       |
| E04 | `E04_attack_receipt_cloud.png`     | **CloudWatch** contains deny receipt for 403 (audit trail exists in cloud runtime)                                   |
| E05 | `E05_alarms.png`                   | **Operational guardrails**: CloudWatch alarms for 5xx, throttles, and high denials configured                                 |
| E06 | `E06_jwt_whoami.png`               | **JWT mode** `/whoami`: principal derived from **verified JWT claims** (tenant/role not client-asserted)                       |
| E07 | `E07_jwt_attack_receipt_cloud.png` | **JWT-authenticated** deny produces CloudWatch receipt with `reason_code` + `request_id` (correlatable audit evidence) |
| E08 | `E08_redaction_proof.png`          | **Snippet output redaction**: secret/canary is replaced with `[REDACTED]` in returned snippet (no secret egress)        |
