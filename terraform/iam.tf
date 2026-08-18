# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "CloudLabEC2S3Role"
resource "aws_iam_instance_profile" "railguard" {
  name     = "CloudLabEC2S3Role"
  path     = "/"
  role     = "CloudLabEC2S3Role"
  tags     = {}
  tags_all = {}
}

# __generated__ by Terraform from "CloudLabEC2S3Role"
resource "aws_iam_role" "railguard" {
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  description           = "Allows EC2 instances to call AWS services on your behalf."
  force_detach_policies = false
  max_session_duration  = 3600
  name                  = "CloudLabEC2S3Role"
  path                  = "/"
  permissions_boundary  = null
  tags                  = {}
  tags_all              = {}
}
