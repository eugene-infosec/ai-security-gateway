resource "aws_cognito_user_pool" "pool" {
  name = "${local.name}-user-pool"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  # Custom attributes -> appear as "custom:tenant_id" and "custom:role" in JWT claims
  schema {
    name                     = "tenant_id"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false
    string_attribute_constraints {
      min_length = 1
      max_length = 64
    }
  }

  schema {
    name                     = "role"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false
    string_attribute_constraints {
      min_length = 1
      max_length = 32
    }
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "${local.name}-client"
  user_pool_id = aws_cognito_user_pool.pool.id

  generate_secret = false

  # 1. Enable Authentication Flows
  # This allows your script to log in using USERNAME + PASSWORD
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  # 2. CRITICAL FIX: Allow the client to SEE the custom attributes
  # Without this, the JWT token will NOT contain "custom:tenant_id" or "custom:role"
  read_attributes = [
    "email",
    "email_verified",
    "custom:tenant_id",
    "custom:role"
  ]

  # 3. CRITICAL FIX: Allow the client to WRITE the custom attributes
  # Note: We intentionally exclude "email_verified" here because only Cognito can write that.
  write_attributes = [
    "email",
    "custom:tenant_id",
    "custom:role"
  ]

  prevent_user_existence_errors = "ENABLED"
}

locals {
  jwt_issuer   = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.pool.id}"
  jwt_audience = aws_cognito_user_pool_client.client.id
}
