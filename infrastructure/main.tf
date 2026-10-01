module "aws_backend" {
  source = "./modules/aws"

  app_name       = var.app_name
  environment    = var.environment
  image_tag      = var.image_tag
  extension_id   = var.extension_id
  container_host = var.container_host
  container_port = var.container_port
}

# module "github_setup" {
#   source = "./modules/github"

#   github_profile   = var.github_profile
#   github_repo_name = var.github_repo_name
# }
