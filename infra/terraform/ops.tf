# infra/terraform/ops.tf

# 1. Metric Filter: Count "access_denied" events in the logs
resource "aws_cloudwatch_log_metric_filter" "access_denied" {
  name           = "AccessDeniedCount"
  log_group_name = aws_cloudwatch_log_group.logs.name
  pattern        = "{ $.event = \"access_denied\" }"

  metric_transformation {
    name      = "AccessDeniedCount"
    namespace = "AISecurityGateway"
    value     = "1"
  }
}

# 2. Alarm: Security Alert (Too many denials)
resource "aws_cloudwatch_metric_alarm" "high_access_denied" {
  alarm_name          = "ai-gateway-high-denials"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AccessDeniedCount"
  namespace           = "AISecurityGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 5 # Alert if >5 denials in 1 minute
  alarm_description   = "Triggered if multiple access_denied events occur (potential attack)."
}

# 3. Alarm: API Error Rate (5xx on HTTP API)
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "ai-gateway-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx" # HTTP API metric name
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggered on any API Gateway 5xx error."

  dimensions = {
    ApiId = aws_apigatewayv2_api.http.id
  }
}

# 4. Alarm: API Throttles
resource "aws_cloudwatch_metric_alarm" "api_throttles" {
  alarm_name          = "ai-gateway-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggered when API Gateway throttles requests."

  dimensions = {
    ApiId = aws_apigatewayv2_api.http.id
  }
}