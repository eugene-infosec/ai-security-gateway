# infra/terraform/lambda.tf

# IAM ROLE
resource "aws_iam_role" "exec" {
  name = "ai_gateway_role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

# PERMISSIONS
resource "aws_iam_role_policy" "policy" {
  name = "ai_gateway_policy"
  role = aws_iam_role.exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], Effect = "Allow", Resource = "arn:aws:logs:*:*:*" },
      { Action = ["dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem"], Effect = "Allow", Resource = aws_dynamodb_table.docs.arn }
    ]
  })
}

# LOG RETENTION (Cost Guardrail)
resource "aws_cloudwatch_log_group" "logs" {
  name              = "/aws/lambda/ai-security-gateway-dev"
  retention_in_days = 7
}

# LAMBDA FUNCTION
resource "aws_lambda_function" "api" {
  filename         = "${path.module}/../../lambda_function.zip"
  function_name    = "ai-security-gateway-dev"
  role             = aws_iam_role.exec.arn
  handler          = "app.main.handler"
  runtime          = "python3.12"
  timeout          = 10
  source_code_hash = filebase64sha256("${path.module}/../../lambda_function.zip")

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.docs.name
      # --- NEW: Tell the app to use JWT verification in Cloud ---
      AUTH_MODE  = "jwt"
    }
  }
  depends_on = [aws_cloudwatch_log_group.logs]
}