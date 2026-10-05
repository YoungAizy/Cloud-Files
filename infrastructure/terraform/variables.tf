# App variables
variable "app_name" {
  type        = string
  description = "The application name used for resource naming"
  default     = "cloud-save-backend"
}

variable "extension_id" {
  type        = string
  description = "The ID of the chrome extension calling this api service."
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g., dev, prod)"
  default     = "dev"
}

# AWS Variables
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "image_tag" {
  type        = string
  description = "The specific Docker image tag passed by GitHub Actions"
}

variable "instance_type"{
  type        = string
  description = "The AWS EC2 instance type"
}

# --- Container Environment Variables ---
variable "container_host" {
  type        = string
  description = "The IP address to bind the fastapi server to."
}

variable "container_port" {
  type        = string
  description = "The port the Fastapi server should listen to internally to route traffic from lambda."
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
