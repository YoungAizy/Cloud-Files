# 1. Container Registry to hold FastAPI image
resource "aws_ecr_repository" "docker_repo" {
  name                 = "${var.app_name}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "repo_policy" {
  repository = aws_ecr_repository.docker_repo.name

  # Rules must be wrapped into a structured JSON payload
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Immediately delete untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 5
        description  = "Keep only 1 test images at a time"
        selection = {
          tagStatus   = "tagged"
          tagPrefixList = ["test"]
          countType   = "imageCountMoreThan"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Keep only 3 dev images at a time"
        selection = {
          tagStatus   = "tagged"
          tagPrefixList = ["dev-"]
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep only the last 5 prod tagged deployment images to save space"
        selection = {
          tagStatus   = "tagged"
          tagPrefixList = ["prod-"]
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# 2. IAM Execution Role allowing Lambda to run and write logs
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.app_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Attach CloudWatch log permissions to the Execution Role
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 3. The Core Lambda Resource running your container image
resource "aws_lambda_function" "fastapi_lambda" {
  function_name = "${var.app_name}-${var.environment}"
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  architectures = ["x86_64"] # Matches standard GitHub runner compilation builds
  
  # Combines ECR URL and GitHub Action variable tag to deploy the exact version
  image_uri = "${aws_ecr_repository.docker_repo.repository_url}:${var.image_tag}"

  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_logs]
}

# 4. HTTPS Endpoint Generator (Lambda Function URL)
resource "aws_lambda_function_url" "api_endpoint" {
  function_name      = aws_lambda_function.fastapi_lambda.function_name
  authorization_type = "NONE" # Allows standard web traffic (public API)

  cors {
    allow_credentials = true
    allow_origins     = ["chrome-extension://${var.extension_id}"]
    allow_methods     = ["*"]
    allow_headers     = ["*"]
  }
}
