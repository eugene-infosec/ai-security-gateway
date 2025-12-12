# Cost Analysis & Operational Guardrails

This document outlines the estimated monthly run rate and the controls in place to prevent billing surprises.

## 💰 Estimated Run Rate (Idle)
| Service      | Logic                               | Est. Cost      |
| :----------- | :---------------------------------- | :------------- |
| **Lambda** | Free Tier (400k GB-s/mo)            | $0.00          |
| **API Gateway** | HTTP API Free Tier (1M req/mo)   | $0.00          |
| **CloudWatch** | Logs (5GB free) + 3 alarms       | ~$0.30         |
| **Cognito** | MAU Free Tier (50k users)           | $0.00          |
| **Total** |                                    | **<$1.00 / mo** |

> Assumes dev traffic stays well within AWS Free Tier limits.

## 🛡️ Operational Guardrails

1. **API Throttling**: Hard limit of **50 req/sec** enforced at the Gateway edge.
2. **Log Retention**: Logs expire after **7 days** to cap storage.
3. **Alarms**: Alerts configured for:
   - **Security Spikes** (`access_denied` metric)
   - **Availability** (5xx errors)
   - **Abuse / Load** (API throttles)
4. **Kill Switch**: `make destroy-dev` destroys all resources immediately.