// Compliance-Aligned Data Access Gateway - Azure Reference Architecture
// Reference implementation - NOT deployed in this demo
//
// This Bicep template shows the Azure-native equivalent of the AWS implementation.
// The same security invariants (Auth-Before-Retrieval, tenant isolation, audit receipts)
// apply regardless of cloud provider.

targetScope = 'resourceGroup'

// Parameters
@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Project name prefix')
param projectName string = 'ai-gateway'

// Variables
var resourcePrefix = '${projectName}-${environment}'
var functionAppName = '${resourcePrefix}-func'
var appServicePlanName = '${resourcePrefix}-plan'
var storageAccountName = replace('${resourcePrefix}sa', '-', '')
var logAnalyticsName = '${resourcePrefix}-logs'
var apimName = '${resourcePrefix}-apim'

// Log Analytics Workspace (equivalent to CloudWatch Logs)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 7 // Match AWS 7-day retention
  }
}

// Storage Account for Function App
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// Consumption App Service Plan (equivalent to Lambda scale-to-zero)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true // Linux
  }
}

// Function App (equivalent to Lambda)
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      pythonVersion: '3.12'
      linuxFxVersion: 'PYTHON|3.12'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=core.windows.net;AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AUTH_MODE'
          value: 'jwt'
        }
        {
          name: 'LOG_LEVEL'
          value: 'INFO'
        }
      ]
    }
  }
}

// API Management (equivalent to API Gateway + JWT Authorizer)
// Note: APIM Consumption tier for cost efficiency
resource apim 'Microsoft.ApiManagement/service@2023-03-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: 'admin@example.com'
    publisherName: 'AI Gateway'
  }
}

// APIM API Definition
resource api 'Microsoft.ApiManagement/service/apis@2023-03-01-preview' = {
  parent: apim
  name: 'gateway-api'
  properties: {
    displayName: 'Data Access Gateway API'
    path: 'gateway'
    protocols: ['https']
    subscriptionRequired: false // JWT handles auth
  }
}

// JWT Validation Policy (equivalent to API Gateway JWT Authorizer)
// This policy validates Entra ID tokens
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-03-01-preview' = {
  parent: api
  name: 'policy'
  properties: {
    value: '''
      <policies>
        <inbound>
          <base />
          <!-- JWT Validation - Entra ID -->
          <validate-jwt header-name="Authorization" failed-validation-httpcode="401">
            <openid-config url="https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" />
            <required-claims>
              <claim name="aud" match="any">
                <value>{client-id}</value>
              </claim>
            </required-claims>
          </validate-jwt>
          <!-- Extract claims for downstream -->
          <set-header name="X-Tenant-Id" exists-action="override">
            <value>@(context.Request.Headers.GetValueOrDefault("Authorization","").AsJwt()?.Claims.GetValueOrDefault("tenant_id", "unknown"))</value>
          </set-header>
          <set-header name="X-Role" exists-action="override">
            <value>@(context.Request.Headers.GetValueOrDefault("Authorization","").AsJwt()?.Claims.GetValueOrDefault("roles", "unknown"))</value>
          </set-header>
        </inbound>
        <backend>
          <base />
        </backend>
        <outbound>
          <base />
        </outbound>
      </policies>
    '''
    format: 'xml'
  }
}

// Health endpoint - no auth required (matches AWS /health public route)
resource healthOperation 'Microsoft.ApiManagement/service/apis/operations@2023-03-01-preview' = {
  parent: api
  name: 'health'
  properties: {
    displayName: 'Health Check'
    method: 'GET'
    urlTemplate: '/health'
  }
}

// Health endpoint policy - skip JWT validation
resource healthPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-03-01-preview' = {
  parent: healthOperation
  name: 'policy'
  properties: {
    value: '''
      <policies>
        <inbound>
          <base />
          <!-- No JWT validation for health check -->
        </inbound>
        <backend>
          <base />
        </backend>
        <outbound>
          <base />
        </outbound>
      </policies>
    '''
    format: 'xml'
  }
}

// Outputs
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output apimGatewayUrl string = apim.properties.gatewayUrl
output logAnalyticsWorkspaceId string = logAnalytics.id
