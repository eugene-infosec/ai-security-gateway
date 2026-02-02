# Azure Reference Architecture

> **Status:** Reference implementation - NOT deployed in this demo.

This directory contains Bicep templates showing the Azure-native equivalent of the AWS implementation.

## What's Here

| File | Purpose |
|------|---------|
| `main.bicep` | Function App + APIM + Entra ID JWT validation + Log Analytics |

## AWS to Azure Mapping

| AWS Component | Azure Equivalent | Notes |
|---------------|------------------|-------|
| Lambda | Azure Functions (Consumption) | Scale-to-zero |
| API Gateway + JWT Authorizer | APIM + `validate-jwt` policy | Edge JWT validation |
| Cognito | Entra ID (Azure AD) | Identity provider |
| CloudWatch Logs | Log Analytics | 7-day retention |
| CloudWatch Alarms | Azure Monitor Alerts | (not included in skeleton) |

## Why Not Deployed

1. **Reviewer friction:** Azure deployment requires additional setup (subscription, Entra ID app registration)
2. **Orthogonal to thesis:** The security invariants are cloud-agnostic
3. **Signal over completeness:** The Bicep template proves Azure fluency without requiring deployment

## How to Deploy (if desired)

```bash
# Login to Azure
az login

# Create resource group
az group create --name ai-gateway-rg --location canadacentral

# Deploy
az deployment group create \
  --resource-group ai-gateway-rg \
  --template-file main.bicep \
  --parameters environment=dev

# Cleanup
az group delete --name ai-gateway-rg --yes
```

## Key Differences from AWS

1. **JWT validation:** APIM uses inline XML policy vs API Gateway's built-in authorizer
2. **Claims extraction:** APIM policy extracts claims into headers for downstream use
3. **Cold starts:** Azure Functions Consumption has similar cold-start characteristics to Lambda

## See Also

- [Azure Enterprise Mapping](../../docs/azure_mapping.md) - conceptual mapping
- [Azure Sentinel Queries](../../docs/azure_sentinel_queries.md) - KQL examples for detection
