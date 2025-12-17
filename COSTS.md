# Costs
> Truth scope: accurate as of **v0.3.0** (dev demo)

This repo is designed to be cheap-by-default (serverless, short log retention, fast teardown).

## Cost controls
- Kill switch: `make destroy-dev` (run after every demo)
- CloudWatch log retention is set (7 days)
- Alarms exist to surface errors/throttles/deny spikes

## Notes
Actual AWS cost depends on request volume and AWS pricing. Use AWS Billing / Cost Explorer if you need exact numbers during longer testing.
