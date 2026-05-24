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

    filter {}

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
