
terraform {
  backend "s3" {
    bucket         = var.bucket_name
    key            = var.key_name 
    region         = var.aws_region                 
  }
}
