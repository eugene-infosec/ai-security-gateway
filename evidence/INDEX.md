# Evidence Artifact Index
> All artifacts are referenced by ID to ensure traceability. Filenames match the "Master Plan" documentation.

| ID  | File | Claim / Proof |
| :-- | :--- | :------------ |
| E00 | `INDEX.md` | This index file |
| E01 | `E01_attack_receipt_local.png` | Local deny receipt (structured log) |
| E02 | `E02_gate_pass_local.png` | Security gates passing locally (`make gate`) |
| E03 | `E03_smoke_dev_output.png` | Dev smoke passes against AWS (`make smoke-dev`) |
| E04 | `E04_attack_receipt_cloud.png` | CloudWatch deny receipt exists (403) |
| E05 | `E05_alarms.png` | CloudWatch alarms (errors/throttles/high denials) |
| E06 | `jwt_attack_receipt.png` | CloudWatch deny receipt for JWT user |
| E07 | `alarms.png` | CloudWatch alarms (Ops Guardrails) |
