resource "aws_cloudwatch_metric_alarm" "railguard_high_memory" {
  alarm_name          = "RailGuard-High-Memory"
  alarm_description   = "RailGuard AI EC2 memory usage above 80% for 3 consecutive minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 80
  metric_name         = "mem_used_percent"
  namespace           = "RailGuardAI"
  period              = 60
  statistic           = "Average"
  treat_missing_data  = "notBreaching"

  alarm_actions = [
    "arn:aws:sns:eu-north-1:443920089735:RailGuard-Alerts"
  ]

  dimensions = {
    InstanceId = "i-0e9b285cb2a403781"
  }
}
