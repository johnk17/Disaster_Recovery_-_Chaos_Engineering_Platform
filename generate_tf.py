import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content.strip() + '\n')

vpc_main = """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs             = var.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = false
  enable_vpn_gateway = false

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}
"""

vpc_vars = """
variable "vpc_name" { type = string, default = "dr-chaos-vpc" }
variable "vpc_cidr" { type = string, default = "10.0.0.0/16" }
variable "azs" { type = list(string), default = ["us-east-1a", "us-east-1b", "us-east-1c"] }
variable "private_subnets" { type = list(string), default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"] }
variable "public_subnets" { type = list(string), default = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"] }
"""

vpc_outputs = """
output "vpc_id" { value = module.vpc.vpc_id }
output "private_subnets" { value = module.vpc.private_subnets }
output "public_subnets" { value = module.vpc.public_subnets }
"""

eks_main = """
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  vpc_id                   = var.vpc_id
  subnet_ids               = var.private_subnets
  control_plane_subnet_ids = var.public_subnets

  cluster_endpoint_public_access  = true

  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["t3.medium"]
  }

  eks_managed_node_groups = {
    main = {
      min_size     = 2
      max_size     = 6
      desired_size = 2
    }
  }

  enable_irsa = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
  }
}
"""

eks_vars = """
variable "cluster_name" { type = string, default = "dr-chaos-eks" }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "public_subnets" { type = list(string) }
"""

eks_outputs = """
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "cluster_certificate_authority_data" { value = module.eks.cluster_certificate_authority_data }
output "cluster_name" { value = module.eks.cluster_name }
output "oidc_provider_arn" { value = module.eks.oidc_provider_arn }
"""

iam_main = """
module "vpc_cni_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "vpc-cni"
  attach_vpc_cni_policy = true
  vpc_cni_enable_ipv4 = true

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-node"]
    }
  }
}

module "external_dns_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                     = "external-dns"
  attach_external_dns_policy    = true

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["kube-system:external-dns"]
    }
  }
}

module "velero_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name             = "velero"
  attach_velero_policy  = true
  velero_s3_bucket_arns = [var.velero_bucket_arn]

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["velero:velero"]
    }
  }
}
"""

iam_vars = """
variable "oidc_provider_arn" { type = string }
variable "velero_bucket_arn" { type = string }
"""

jenkins_main = """
resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-sg"
  description = "Allow Jenkins inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    description = "Jenkins web UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.jenkins_allowed_ip]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.jenkins_allowed_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_iam_role" "jenkins_role" {
  name = "jenkins_ec2_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "jenkins_policy" {
  name = "jenkins_ec2_policy"
  role = aws_iam_role.jenkins_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "eks:DescribeCluster"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "jenkins_profile" {
  name = "jenkins_ec2_profile"
  role = aws_iam_role.jenkins_role.name
}

resource "aws_instance" "jenkins" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.medium"
  subnet_id     = var.subnet_id

  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.jenkins_profile.name

  root_block_device {
    volume_type = "gp3"
    volume_size = 50
  }

  user_data = <<-EOF
    #!/bin/bash
    sudo yum update -y
    sudo yum install -y docker java-21-amazon-corretto maven git wget jq
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker ec2-user
    
    # Install kubectl
    curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
    chmod +x ./kubectl
    sudo mv ./kubectl /usr/local/bin/kubectl

    # Run Jenkins
    mkdir -p /var/jenkins_home
    chown -R 1000:1000 /var/jenkins_home
    docker run -d --name jenkins -p 8080:8080 -p 50000:50000 -v /var/jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock jenkins/jenkins:lts-jdk21
  EOF
}

resource "aws_eip" "jenkins_eip" {
  instance = aws_instance.jenkins.id
  domain   = "vpc"
}
"""

jenkins_vars = """
variable "vpc_id" { type = string }
variable "subnet_id" { type = string }
variable "jenkins_allowed_ip" { type = string, default = "0.0.0.0/0" }
"""

jenkins_outputs = """
output "jenkins_url" {
  value = "http://${aws_eip.jenkins_eip.public_ip}:8080"
}
"""

main_tf = """
provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source = "./modules/vpc"
}

module "eks" {
  source          = "./modules/eks"
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets
}

module "jenkins" {
  source             = "./modules/jenkins-ec2"
  vpc_id             = module.vpc.vpc_id
  subnet_id          = module.vpc.public_subnets[0]
  jenkins_allowed_ip = var.jenkins_allowed_ip
}

resource "aws_s3_bucket" "velero" {
  bucket_prefix = "velero-backup-"
}

resource "aws_s3_bucket_versioning" "velero" {
  bucket = aws_s3_bucket.velero.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "velero" {
  bucket = aws_s3_bucket.velero.id

  rule {
    id     = "retention"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

module "iam" {
  source            = "./modules/iam"
  oidc_provider_arn = module.eks.oidc_provider_arn
  velero_bucket_arn = aws_s3_bucket.velero.arn
}
"""

root_vars = """
variable "jenkins_allowed_ip" {
  type    = string
  default = "0.0.0.0/0"
}
"""

root_outputs = """
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}
output "velero_s3_bucket" {
  value = aws_s3_bucket.velero.id
}
output "jenkins_url" {
  value = module.jenkins.jenkins_url
}
output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region us-east-1 --name ${module.eks.cluster_name}"
}
"""

tfvars = """
jenkins_allowed_ip = "0.0.0.0/0"
"""


base = "c:/dr-chaos-platform/terraform"
write_file(f"{base}/modules/vpc/main.tf", vpc_main)
write_file(f"{base}/modules/vpc/variables.tf", vpc_vars)
write_file(f"{base}/modules/vpc/outputs.tf", vpc_outputs)

write_file(f"{base}/modules/eks/main.tf", eks_main)
write_file(f"{base}/modules/eks/variables.tf", eks_vars)
write_file(f"{base}/modules/eks/outputs.tf", eks_outputs)

write_file(f"{base}/modules/iam/main.tf", iam_main)
write_file(f"{base}/modules/iam/variables.tf", iam_vars)
write_file(f"{base}/modules/iam/outputs.tf", "")

write_file(f"{base}/modules/jenkins-ec2/main.tf", jenkins_main)
write_file(f"{base}/modules/jenkins-ec2/variables.tf", jenkins_vars)
write_file(f"{base}/modules/jenkins-ec2/outputs.tf", jenkins_outputs)

write_file(f"{base}/main.tf", main_tf)
write_file(f"{base}/variables.tf", root_vars)
write_file(f"{base}/outputs.tf", root_outputs)
write_file(f"{base}/terraform.tfvars", tfvars)

print("Terraform files generated successfully.")
