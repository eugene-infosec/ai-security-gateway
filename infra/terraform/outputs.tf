output "base_url" {
  value = aws_apigatewayv2_stage.stage.invoke_url
}

output "lambda_log_group" {
  value = aws_cloudwatch_log_group.lambda.name
}
