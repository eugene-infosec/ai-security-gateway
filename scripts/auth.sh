#!/usr/bin/env bash
set -euo pipefail

CLIENT_ID="$(terraform -chdir=infra/terraform output -raw cognito_user_pool_client_id)"

read -p "Username: " USERNAME
read -s -p "Password: " PASSWORD
echo

JSON="$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$CLIENT_ID" \
  --auth-parameters "USERNAME=$USERNAME,PASSWORD=$PASSWORD")"

JWT_TOKEN="$(echo "$JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")"
export JWT_TOKEN
echo "✅ JWT_TOKEN exported (IdToken)."
