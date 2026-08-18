# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "cloudlab-api-data-443920089735-eu-north-1-an"
resource "aws_s3_bucket_public_access_block" "railguard" {
  block_public_acls       = true
  block_public_policy     = true
  bucket                  = "cloudlab-api-data-443920089735-eu-north-1-an"
  ignore_public_acls      = true
  region                  = "eu-north-1"
  restrict_public_buckets = true
  skip_destroy            = null
}

# __generated__ by Terraform from "cloudlab-api-data-443920089735-eu-north-1-an"
resource "aws_s3_bucket_server_side_encryption_configuration" "railguard" {
  bucket = "cloudlab-api-data-443920089735-eu-north-1-an"
  region = "eu-north-1"
  rule {
    blocked_encryption_types = ["SSE-C"]
    bucket_key_enabled       = true
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
