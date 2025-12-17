resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id          = aws_apigatewayv2_api.http_api.id
  name            = "${local.name}-jwt-authorizer"
  authorizer_type = "JWT"

  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [local.jwt_audience]
    issuer   = local.jwt_issuer
  }
}
