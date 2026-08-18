# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "CloudLabEC2S3Role:RailGuardTerraformInventory"
resource "aws_iam_role_policy" "terraform_inventory" {
  name = "RailGuardTerraformInventory"
  policy = jsonencode({
    Statement = [{
      Action   = ["ec2:Describe*"]
      Effect   = "Allow"
      Resource = "*"
      Sid      = "RailGuardEC2Inventory"
      }, {
      Action   = ["iam:GetRole", "iam:ListAttachedRolePolicies", "iam:ListRolePolicies", "iam:GetRolePolicy"]
      Effect   = "Allow"
      Resource = "arn:aws:iam::443920089735:role/CloudLabEC2S3Role"
      Sid      = "RailGuardIAMRoleInventory"
      }, {
      Action   = ["iam:GetInstanceProfile"]
      Effect   = "Allow"
      Resource = "arn:aws:iam::443920089735:instance-profile/CloudLabEC2S3Role"
      Sid      = "RailGuardInstanceProfileInventory"
      }, {
      Action   = ["s3:Get*", "s3:ListBucket"]
      Effect   = "Allow"
      Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an"
      Sid      = "RailGuardS3Inventory"
    }]
    Version = "2012-10-17"
  })
  role = "CloudLabEC2S3Role"
}

# __generated__ by Terraform from "CloudLabEC2S3Role:CloudLabS3Access"
resource "aws_iam_role_policy" "s3_access" {
  name = "CloudLabS3Access"
  policy = jsonencode({
    Statement = [{
      Action   = ["s3:ListBucket"]
      Effect   = "Allow"
      Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an"
      }, {
      Action   = ["s3:PutObject", "s3:GetObject"]
      Effect   = "Allow"
      Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an/*"
    }]
    Version = "2012-10-17"
  })
  role = "CloudLabEC2S3Role"
}

# __generated__ by Terraform from "CloudLabEC2S3Role:RailGuardCloudWatchAlarmPolicy"
resource "aws_iam_role_policy" "cloudwatch_alarm" {
  name = "RailGuardCloudWatchAlarmPolicy"
  policy = jsonencode({
    Statement = [{
      Action   = ["cloudwatch:PutMetricAlarm", "cloudwatch:DescribeAlarms", "cloudwatch:DeleteAlarms"]
      Effect   = "Allow"
      Resource = "*"
    }]
    Version = "2012-10-17"
  })
  role = "CloudLabEC2S3Role"
}
