# Azure Sentinel / Log Analytics Queries

> Truth scope: accurate as of **v1.0.0**.

These KQL (Kusto Query Language) examples show how to detect and investigate security events from the gateway when deployed to Azure. They are the Azure-native equivalent of CloudWatch Logs insights.

---

## Prerequisites

- Gateway logs ingested into Log Analytics workspace
- Structured JSON logs with fields: `event`, `reason_code`, `request_id`, `tenant_id`, `role`

---

## Detection Queries

### 1. Access Denied Spike by Tenant

Detect unusual spikes in denied requests, which may indicate misconfiguration or attack.

```kusto
// Alert on access_denied spikes by tenant (5-minute windows)
CustomLogs
| where event == "access_denied"
| summarize DenyCount = count() by tenant_id, bin(TimeGenerated, 5m)
| where DenyCount > 10
| order by DenyCount desc
```

### 2. Fail-Closed Events (Unknown Role)

Detect requests where the role was unknown, triggering fail-closed behavior.

```kusto
// Fail-closed events - unknown roles
CustomLogs
| where reason_code == "ROLE_UNKNOWN_FAIL_CLOSED"
| summarize Count = count() by tenant_id, user_id, bin(TimeGenerated, 1h)
| order by Count desc
```

### 3. Classification Forbidden Events

Detect attempts to access content above the requester's classification level.

```kusto
// Classification forbidden - privilege escalation attempts
CustomLogs
| where reason_code == "CLASSIFICATION_FORBIDDEN"
| project TimeGenerated, request_id, tenant_id, user_id, role, path
| order by TimeGenerated desc
```

---

## Investigation Queries

### 4. Request Tracing by ID

Reconstruct the full journey of a specific request.

```kusto
// Trace a single request
let targetRequestId = "abc-123-def-456";
CustomLogs
| where request_id == targetRequestId
| project TimeGenerated, event, reason_code, tenant_id, user_id, role, path
| order by TimeGenerated asc
```

### 5. User Activity Timeline

View all activity for a specific user.

```kusto
// User activity timeline
let targetUserId = "user-12345";
CustomLogs
| where user_id == targetUserId
| summarize Events = count() by event, bin(TimeGenerated, 1h)
| order by TimeGenerated desc
```

### 6. Tenant Activity Summary

Overview of all activity within a tenant.

```kusto
// Tenant activity breakdown
CustomLogs
| where tenant_id == "tenant-a"
| summarize
    TotalRequests = count(),
    Denials = countif(event == "access_denied"),
    Queries = countif(event == "query_allowed"),
    Ingests = countif(event == "doc_ingested")
| extend DenyRate = round(100.0 * Denials / TotalRequests, 2)
```

---

## Alerting Rules

### High Denial Rate Alert

Create an Azure Monitor alert when deny rate exceeds threshold.

```kusto
// Use as alert condition
CustomLogs
| where TimeGenerated > ago(5m)
| summarize
    TotalRequests = count(),
    Denials = countif(event == "access_denied")
| where TotalRequests > 10
| extend DenyRate = 100.0 * Denials / TotalRequests
| where DenyRate > 20
```

### Cross-Tenant Access Attempt

This should never happen - any result indicates a potential bug or attack.

```kusto
// Should return 0 results if tenant isolation is working
CustomLogs
| where event == "access_denied"
| where reason_code contains "TENANT"
| project TimeGenerated, request_id, tenant_id, user_id
```

---

## Workbook Integration

These queries can be embedded in an Azure Workbook for dashboarding:

1. **Security Overview:** Denial rates, top denied users, classification breakdown
2. **Tenant Health:** Per-tenant activity, deny spikes, user counts
3. **Incident Investigation:** Request tracing, user timelines, correlation views

---

## See Also

- [Azure Enterprise Mapping](./azure_mapping.md) - AWS to Azure conceptual mapping
- [Azure Bicep Reference](../infra/bicep/README.md) - Infrastructure-as-Code
- [Controls Catalog](./controls.md) - What these queries are detecting
