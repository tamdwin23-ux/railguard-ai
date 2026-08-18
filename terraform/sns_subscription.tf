resource "aws_sns_topic_subscription" "railguard_email" {
  topic_arn = "arn:aws:sns:eu-north-1:443920089735:RailGuard-Alerts"
  protocol  = "email"
  endpoint  = "edwintamia377@gmail.com"

  lifecycle {
    ignore_changes = [
      confirmation_timeout_in_minutes,
      endpoint_auto_confirms
    ]
  }
}
