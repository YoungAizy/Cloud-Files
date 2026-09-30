
terraform {
  backend "s3" {
    # Dynamically inject configuration via circleci 
  }
}
