# Evidence Artifact Index
> All artifacts are referenced by ID to ensure traceability. Filenames match the "Master Plan" documentation.

| ID  | File | Claim / Proof |
| :-- | :--- | :------------ |
| E00 | `INDEX.md` | This index file |
| E01 | `attack_receipt.png` | Local deny receipt fields (`event`, `reason_code`, `request_id`) |
| E02 | `ci_gate_fail.png` | CI blocks regression (admin leakage) |
| E03 | `attack_receipt_cloud.png` | AWS CloudWatch log showing deny receipt |
| E04 | `smoke_dev_output.png` | Successful `make smoke-dev` execution |
| E05 | `jwt_whoami.png` | JWT-based identity derivation proof |
| E06 | `jwt_attack_receipt.png` | CloudWatch deny receipt for JWT user |
| E07 | `alarms.png` | CloudWatch alarms (Ops Guardrails) |
