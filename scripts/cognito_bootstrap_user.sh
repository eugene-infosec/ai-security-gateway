#!/usr/bin/env bash
set -euo pipefail

POOL_ID="$(terraform -chdir=infra/terraform output -raw cognito_user_pool_id)"
REGION="$(terraform -chdir=infra/terraform output -json 2>/dev/null | jq -r 'empty' >/dev/null 2>&1 || true)"

USERNAME="${1:-test-intern}"
TENANT_ID="${2:-tenant-a}"
ROLE="${3:-intern}"

echo "Using User Pool: $POOL_ID"
echo "Creating/Updating user: $USERNAME (tenant=$TENANT_ID role=$ROLE)"

aws cognito-idp admin-create-user \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --user-attributes \
    Name="custom:tenant_id",Value="$TENANT_ID" \
    Name="custom:role",Value="$ROLE" \
  --message-action SUPPRESS >/dev/null 2>&1 || true

# Prompt for password without echo
read -s -p "Set password for $USERNAME (min 12, mixed chars): " PASSWORD
echo
aws cognito-idp admin-set-user-password \
  --user-pool-id "$POOL_ID" \
  --username "$USERNAME" \
  --password "$PASSWORD" \
  --permanent >/dev/null

echo "✅ User ready."
