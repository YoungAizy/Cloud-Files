output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions_oidc.arn
  description = "The IAM Role ARN for your GitHub Actions workflow configuration."
}