module "aws_backend" {
  source = "./modules/aws"

  app_name       = var.app_name
  environment    = var.environment
  extension_id   = var.extension_id
  image_tag      = var.image_tag
  container_host = var.container_host
  container_port = var.container_port
  aws_region     = var.aws_region
  instance_type  = var.instance_type
}

# module "github_setup" {
#   source = "./modules/github"

#   github_profile   = var.github_profile
#   github_repo_name = var.github_repo_name
# }
