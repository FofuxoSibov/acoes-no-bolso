variable "project_name" { type = string }
variable "environment" { type = string }
variable "instance_type" { type = string }
variable "vpc_id" { type = string, default = null }
variable "subnet_id" { type = string, default = null }

variable "github_repo_url" { type = string }
variable "env_file_content" { type = string }
variable "google_credentials_content" { type = string }
