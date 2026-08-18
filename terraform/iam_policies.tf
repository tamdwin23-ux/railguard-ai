resource "aws_iam_role_policy" "terraform_inventory" {
  name = "RailGuardTerraformInventory"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid      = "ReadEC2"
        Effect   = "Allow"
        Action   = ["ec2:Describe*"]
        Resource = "*"
      },
      {
        Sid    = "ReadRailGuardIAMRoles"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:ListAttachedRolePolicies",
          "iam:ListRolePolicies",
          "iam:GetRolePolicy"
        ]
        Resource = [
          "arn:aws:iam::443920089735:role/CloudLabEC2S3Role",
          "arn:aws:iam::443920089735:role/RailGuardGitHubDeployRole"
        ]
      },
      {
        Sid      = "ReadInstanceProfile"
        Effect   = "Allow"
        Action   = ["iam:GetInstanceProfile"]
        Resource = "arn:aws:iam::443920089735:instance-profile/CloudLabEC2S3Role"
      },
      {
        Sid      = "ReadGitHubOIDC"
        Effect   = "Allow"
        Action   = ["iam:GetOpenIDConnectProvider"]
        Resource = "arn:aws:iam::443920089735:oidc-provider/token.actions.githubusercontent.com"
      },
      {
        Sid      = "ReadRailGuardS3"
        Effect   = "Allow"
        Action   = ["s3:Get*", "s3:ListBucket"]
        Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an"
      }
    ]
  })

  role = "CloudLabEC2S3Role"
}

resource "aws_iam_role_policy" "s3_access" {
  name = "CloudLabS3Access"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::cloudlab-api-data-443920089735-eu-north-1-an/*"
      }
    ]
  })

  role = "CloudLabEC2S3Role"
}

resource "aws_iam_role_policy" "cloudwatch_alarm" {
  name = "RailGuardCloudWatchAlarmPolicy"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:DeleteAlarms"
        ]
        Resource = "*"
      }
    ]
  })

  role = "CloudLabEC2S3Role"
}
