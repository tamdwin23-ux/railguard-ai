variable "aws_region" {
  description = "AWS region used by RailGuard AI"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
