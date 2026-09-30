variable "app_name" {
  type        = string
  description = "The application name used for resource naming"
  default     = "cloud-save-backend"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g., dev, prod)"
  default     = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "image_tag" {
  type        = string
  description = "The specific Docker image tag passed by GitHub Actions"
}

variable "extension_id" {
  type        = string
  description = "The ID of the chrome extension calling this api service."
}

# --- Github Configuration ---
variable "github_profile" {
  type        = string
  description = "The GitHub profile name we'll be pushing code to."
}

variable "github_repo_name" {
  type        = string
  description = "The GitHub repository name (e.g., 'my-fastapi-app')"
}

# --- GCP Configuration Placeholders ---
variable "gcp_project_id" {
  type    = string
  default = "my-future-gcp-project"
}

variable "gcp_region" {
  type    = string
  default = "us-central1"
}
