output "aws_api_endpoint" {
  value       = module.aws_backend.api_url
  description = "The public endpoint for your AWS FastAPI application"
}
