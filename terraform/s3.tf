# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "cloudlab-api-data-443920089735-eu-north-1-an"
resource "aws_s3_bucket" "railguard" {
  bucket              = "cloudlab-api-data-443920089735-eu-north-1-an"
  bucket_namespace    = "account-regional"
  force_destroy       = false
  object_lock_enabled = false
  region              = "eu-north-1"
  tags                = {}
  tags_all            = {}
}
