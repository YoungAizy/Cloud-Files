data "aws_iam_openid_connect_provider" "github" {
 url = "https://token.actions.githubusercontent.com"
}

# resource "aws_iam_openid_connect_provider" "github" {
#     url             = "https://githubusercontent.com"
#     client_id_list  = ["://amazonaws.com"]
#     thumbprint_list = ["1c58a3a8518e8759bf075b76b750d4f2df264fcd", "6938fd4d98bab03faadb97b34396831e3780aea1"]
# }

resource "aws_iam_role" "github_actions_oidc" {
  name = "github-actions-deploy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "://amazonaws.com"
          }
          StringLike = {
            # Restricts role assumption strictly to your repository's main branch
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_profile}/${var.github_repo_name}:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

# Attach permissions to the Deployment Role 
# resource "aws_iam_role_policy_attachment" "github_admin" {
#   role       = aws_iam_role.github_actions_oidc.name
#   policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" 
# }

# Attach AWS Lambda Full Access permissions
resource "aws_iam_role_policy_attachment" "github_lambda" {
  role       = aws_iam_role.github_actions_oidc.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess" 
}

# Attach Amazon ECR Power User permissions (allows push/pulling containers but prevents registry deletion)
resource "aws_iam_role_policy_attachment" "github_ecr" {
  role       = aws_iam_role.github_actions_oidc.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser" 
}