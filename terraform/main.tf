terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "app_server" {
  source = "./modules/ec2_docker"

  project_name  = var.project_name
  environment   = var.environment
  instance_type = var.instance_type
  vpc_id        = var.vpc_id
  subnet_id     = var.subnet_id

  github_repo_url            = var.github_repo_url
  env_file_content           = file("../.env")
  google_credentials_content = file("../credentials/service-account.json")
}

