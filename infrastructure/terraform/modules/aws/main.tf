# Container Registry to hold FastAPI image
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

# IAM Role for EC2 instance
resource "aws_iam_role" "ec2_ecr_role" {
  name = "${var.app_name}-ecr-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.app_name}-instance-profile"
  role = aws_iam_role.ec2_ecr_role.name
}

# Attach policies to role
resource "aws_ecr_repository_policy" "ecr_pull_policy" {
  repository = aws_ecr_repository.docker_repo.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAWSResourcesToPullImage"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ec2_ecr_role.arn
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_read_only" {
  role       = aws_iam_role.ec2_ecr_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role = aws_iam_role.ec2_ecr_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# VPC Setup
resource "aws_vpc" "cloud_save_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = var.app_name}
}

resource "aws_subnet" "cloud_save_public" {
  vpc_id                  = aws_vpc.cloud_save_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = var.aws_region
  tags                    = { Name = var.app_name }
}

resource "aws_internet_gateway" "cloud_save_igw" {
  vpc_id = aws_vpc.cloud_save_vpc.id
  tags   = { Name = var.app_name }
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.cloud_save_vpc.id
  route  = [
    {
      cidr_block = "0.0.0.0/0"
      gateway_id = aws_internet_gateway.cloud_save_igw.id
    }
  ]
  tags   = { Name = var.app_name }
}

resource "aws_route_table_association" "cloud_save_rta" {
  subnet_id      = aws_subnet.cloud_save_public.id
  route_table_id = aws_route_table.public_route_table.id
}

# Setup Security Group
resource "aws_security_group" "cloud_save_public_sg" {
  name        = "${var.app_name}-sg"
  description = "Allow HTTP/HTTPS and SSH"
  vpc_id      = aws_vpc.cloud_save_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }
  
  # allow inbound ssh
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0"]
  }

  # allow outboud traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = 0
    cidr_blocks = [ "0.0.0.0/0"]
  }
}

# EC2 Instance Setup
data "aws_ami" "amazon_ami" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "ec2_instance" {
  ami           = data.aws_ami.amazon_ami.id
  instance_type = var.instance_type
  # key_name      = var.key_pair_name

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  vpc_security_group_ids = [aws_security_group.cloud_save_public_sg.id]
  subnet_id              = aws_subnet.cloud_save_public.id

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install docker -y
              systemctl start docker
              systemctl enable docker
              usermod -a -G docker ec2-user
              EOF

  tags = {
    Name = "${var.app_name}-ec2-instance-${var.environment}"
  }
}


resource "local_file" "ansible_inventory" {
  filename = "${path.module}/../../infrastructure/ansible/hosts.ini"

  content  = templatefile("S{path.module}/../../infrastructure/ansible/hosts.tpl", {
    public_ip    = aws_instance.ec2_instance.id
  })
}