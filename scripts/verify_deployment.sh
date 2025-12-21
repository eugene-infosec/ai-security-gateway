#!/bin/bash
set -e

echo "🔍 1. Auto-Discovering Infrastructure..."
# Get IDs directly from the fresh deployment
POOL_ID=$(aws cognito-idp list-user-pools --max-results 20 --region us-west-2 --query "UserPools[?contains(Name, 'ai-security-gateway-dev')].Id" --output text)
CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id $POOL_ID --region us-west-2 --query "UserPoolClients[0].ClientId" --output text)
API_ID=$(aws apigatewayv2 get-apis --region us-west-2 --query "Items[?Name=='ai-security-gateway-dev'].ApiId" --output text)
API_URL="https://$API_ID.execute-api.us-west-2.amazonaws.com/dev"

echo "   Pool ID:   $POOL_ID"
echo "   Client ID: $CLIENT_ID"
echo "   API URL:   $API_URL"

echo "👤 2. Creating Test User 'test-intern'..."
# Create user (suppress error if exists)
aws cognito-idp admin-create-user \
    --user-pool-id $POOL_ID \
    --username test-intern \
    --user-attributes Name=email,Value=test-intern@example.com Name=email_verified,Value=true \
    --region us-west-2 \
    --message-action SUPPRESS > /dev/null 2>&1 || true

# Set Password
aws cognito-idp admin-set-user-password \
    --user-pool-id $POOL_ID \
    --username test-intern \
    --password "TestIntern123!" \
    --region us-west-2 \
    --permanent

# Assign Attributes
# This works now because Terraform authorized the client to read/write these attributes
aws cognito-idp admin-update-user-attributes \
    --user-pool-id $POOL_ID \
    --username test-intern \
    --region us-west-2 \
    --user-attributes Name="custom:tenant_id",Value="tenant-a" Name="custom:role",Value="intern"

echo "🔑 3. Authenticating..."
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --region us-west-2 \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id $CLIENT_ID \
    --auth-parameters USERNAME=test-intern,PASSWORD="TestIntern123!") # pragma: allowlist secret

# EXTRACT THE ID TOKEN (This is the critical fix: IdToken contains the custom claims)
JWT_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"IdToken": "[^"]*' | cut -d'"' -f4)

echo "⚔️ 4. Launching Attack..."
curl -i -X POST "$API_URL/ingest" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"CLOUD_HACK","body":"x","classification":"admin"}'
