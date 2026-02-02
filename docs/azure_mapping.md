# Azure Enterprise Mapping

> Truth scope: accurate as of **v1.0.0**.

This reference architecture is deployed on **AWS for demonstration**, but the patterns **map closely** to the Azure enterprise stack commonly used in BC public sector environments.

> **Important framing:** “Data residency” is primarily a **deployment property** (region pinning, egress controls, and logging destinations), not an application feature. The gateway’s role is enforcing **identity-first scope**, **safe telemetry**, and **audit-ready receipts** regardless of cloud.

---

## Concept mapping (AWS demo → Azure equivalent)

| Pattern / Control Area | AWS (This Demo) | Azure Equivalent |
| :--- | :--- | :--- |
| **Identity Provider** | Cognito User Pool | **Microsoft Entra ID** (Azure AD) |
| **JWT Validation (Edge)** | API Gateway JWT Authorizer | **Azure API Management (APIM)** `validate-jwt` policy |
| **Compute** | AWS Lambda | **Azure Functions** |
| **API Front Door** | API Gateway (HTTP API) | **APIM** (optionally behind App Gateway / Front Door) |
| **Infrastructure-as-Code** | Terraform (`aws` provider) | Terraform (`azurerm` provider) / **Bicep** |
| **Observability** | CloudWatch Logs + Alarms | **Azure Monitor** + Log Analytics + Alerts |
| **SIEM / Detection** | CloudWatch logs → filters/metrics | **Microsoft Sentinel** (KQL queries + analytics rules) |
| **Secrets Management** | (pattern-level) env vars / parameterization | **Azure Key Vault** + managed identity |
| **Policy / Guardrails** | (pattern-level) gates + IaC review | **Azure Policy** + Defender for Cloud |

---

## How the demo’s “audit receipts” translate to Azure

- **Structured JSON logs** emitted by the gateway map directly to:
  - **Log Analytics tables** (via Azure Monitor ingestion)
  - **Sentinel detections** (KQL over `event`, `reason_code`, `request_id`, `tenant_id`, `role`)

**Example use cases:**
- Alert on spikes in `event="access_denied"` by `tenant_id`
- Investigate a single `request_id` to reconstruct a deny path (forensics)
- Detect policy drift by correlating unexpected `ROLE_UNKNOWN_FAIL_CLOSED` events

---

## Public sector note on residency (BC)

Data residency is typically achieved in Azure by:

- Pinning resources to **Canada Central** or **Canada East**
- Ensuring **logs/telemetry** land in Canadian regions (Log Analytics workspace region)
- Enforcing egress restrictions (route controls, private endpoints, firewall policies)

The gateway supports this posture by:
- Keeping enforcement inside a **trusted compute boundary**
- Ensuring sensitive content isn’t emitted via logs/snippets
- Emitting **correlatable receipts** for audit review

---

## Additional Azure Resources

This repo includes Azure-specific reference materials:

| Resource | Location | Purpose |
|----------|----------|---------|
| **Bicep Templates** | `infra/bicep/` | Function App + APIM + Entra ID reference architecture |
| **Sentinel Queries** | `docs/azure_sentinel_queries.md` | KQL examples for detection and investigation |

> **Note:** The Bicep templates are reference implementations showing Azure equivalence, not deployed in this demo.
