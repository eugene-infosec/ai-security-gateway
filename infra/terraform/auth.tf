# infra/terraform/auth.tf

# 1. Cognito User Pool (The Database of Users)
resource "aws_cognito_user_pool" "gateway" {
  name = "ai-security-gateway-users"

  schema {
    name                = "tenant_id"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }
}

# 2. App Client (The "Door" for the API to ask for tokens)
resource "aws_cognito_user_pool_client" "gateway" {
  name         = "ai-security-gateway-client"
  user_pool_id = aws_cognito_user_pool.gateway.id

  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
}

# 3. API Gateway Authorizer (The Bouncer)
resource "aws_apigatewayv2_authorizer" "jwt" {
  # FIX: Reference the "http" resource from api_gateway.tf
  api_id           = aws_apigatewayv2_api.http.id
  name             = "cognito-jwt-authorizer"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.gateway.id]
    issuer   = "https://${aws_cognito_user_pool.gateway.endpoint}"
  }
}

# 4. Outputs (Needed for testing)
output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.gateway.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.gateway.id
}