output "base_url" {
  value = aws_apigatewayv2_stage.stage.invoke_url
}

output "lambda_log_group" {
  value = aws_cloudwatch_log_group.lambda.name
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.pool.id
}

output "cognito_user_pool_client_id" {
  value = aws_cognito_user_pool_client.client.id
}

output "jwt_issuer" {
  value = local.jwt_issuer
}

# REPAIR: Added region output so scripts can auto-detect the deployment target
output "region" {
  value = var.region
}
