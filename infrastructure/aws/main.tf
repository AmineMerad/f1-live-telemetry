# Placeholder. No resources provisioned until the checklist in README.md
# is complete and costs are verified.
terraform {
  required_version = ">= 1.9"
}

variable "aws_region" {
  type        = string
  description = "TODO: select after pricing review"
  default     = "eu-central-1"
}
