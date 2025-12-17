terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  name        = "${var.project_name}-${var.stage}"
  lambda_zip  = "${path.module}/../../dist/lambda.zip"
  log_group   = "/aws/lambda/${local.name}"
  metric_ns   = "AIGateway"
  deny_metric = "AccessDeniedCount"
}

# --- IAM for Lambda ---
resource "aws_iam_role" "lambda_role" {
  name = "${local.name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamo" {
  name = "DynamoDBAccess"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.docs.arn
      }
    ]
  })
}

# --- Data Layer ---
resource "aws_dynamodb_table" "docs" {
  name         = "${local.name}-docs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = {
    Name = "${local.name}-docs"
  }
}

# --- Lambda ---
resource "aws_lambda_function" "gateway" {
  function_name = local.name
  role          = aws_iam_role.lambda_role.arn

  runtime = "python3.12"
  handler = "app.lambda_handler.handler"

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  memory_size = 128
  timeout     = 10

  environment {
    variables = {
      LOG_LEVEL  = "INFO"
      ENV        = var.stage
      TABLE_NAME = aws_dynamodb_table.docs.name
      AUTH_MODE  = "jwt"
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = local.log_group
  retention_in_days = 7
}

# --- API Gateway HTTP API (v2) ---
resource "aws_apigatewayv2_api" "http_api" {
  name          = local.name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = var.stage
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.gateway.invoke_arn
  payload_format_version = "2.0"
}

# --- Routes (Protected vs Public) ---

# 1. Public Health Route (No Auth)
resource "aws_apigatewayv2_route" "health" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /health"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "NONE"
}

# 2. Public OPTIONS (for CORS)
resource "aws_apigatewayv2_route" "options" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "OPTIONS /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# 3. Protected Catch-All (Requires JWT)
resource "aws_apigatewayv2_route" "proxy_jwt" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "ANY /{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id # References authorizer.tf
}

# --- Permissions & Alarms ---

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gateway.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_metric_filter" "deny" {
  name           = "${local.name}-deny-filter"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.event = \"access_denied\" }"

  metric_transformation {
    name      = local.deny_metric
    namespace = local.metric_ns
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name}-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  dimensions = {
    FunctionName = aws_lambda_function.gateway.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  dimensions = {
    FunctionName = aws_lambda_function.gateway.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_denials" {
  alarm_name          = "${local.name}-high-denials"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = local.deny_metric
  namespace           = local.metric_ns
  period              = 60
  statistic           = "Sum"
  threshold           = 5
}
