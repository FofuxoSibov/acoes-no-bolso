variable "aws_region" {
  description = "Região da AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "acoes-no-bolso"
}

variable "environment" {
  description = "Ambiente de deploy (ex: dev, prod)"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "Tipo da instância EC2 (limite t3.medium)"
  type        = string
  default     = "t3.medium"
  validation {
    condition     = contains(["t2.micro", "t3.micro", "t3.small", "t3.medium"], var.instance_type)
    error_message = "O tipo da instância deve ser no máximo t3.medium."
  }
}

variable "vpc_id" {
  description = "ID da VPC existente (opcional, usa a default se vazio)"
  type        = string
  default     = null
}

variable "subnet_id" {
  description = "ID da Subnet existente (opcional)"
  type        = string
  default     = null
}

variable "github_repo_url" {
  description = "URL do repositorio no Github"
  type        = string
}

