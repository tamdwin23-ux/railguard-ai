# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform
resource "aws_sns_topic" "railguard_alerts" {
  application_failure_feedback_role_arn    = null
  application_success_feedback_role_arn    = null
  application_success_feedback_sample_rate = 0
  archive_policy                           = null
  content_based_deduplication              = false
  delivery_policy                          = null
  display_name                             = null
  fifo_topic                               = false
  firehose_failure_feedback_role_arn       = null
  firehose_success_feedback_role_arn       = null
  firehose_success_feedback_sample_rate    = 0
  http_failure_feedback_role_arn           = null
  http_success_feedback_role_arn           = null
  http_success_feedback_sample_rate        = 0
  kms_master_key_id                        = null
  lambda_failure_feedback_role_arn         = null
  lambda_success_feedback_role_arn         = null
  lambda_success_feedback_sample_rate      = 0
  name                                     = "RailGuard-Alerts"
  policy = jsonencode({
    Id = "__default_policy_ID"
    Statement = [{
      Action = ["SNS:GetTopicAttributes", "SNS:SetTopicAttributes", "SNS:AddPermission", "SNS:RemovePermission", "SNS:DeleteTopic", "SNS:Subscribe", "SNS:ListSubscriptionsByTopic", "SNS:Publish"]
      Condition = {
        StringEquals = {
          "AWS:SourceOwner" = "443920089735"
        }
      }
      Effect = "Allow"
      Principal = {
        AWS = "*"
      }
      Resource = "arn:aws:sns:eu-north-1:443920089735:RailGuard-Alerts"
      Sid      = "__default_statement_ID"
    }]
    Version = "2008-10-17"
  })
  region                           = "eu-north-1"
  sqs_failure_feedback_role_arn    = null
  sqs_success_feedback_role_arn    = null
  sqs_success_feedback_sample_rate = 0
  tags                             = {}
  tags_all                         = {}
}
