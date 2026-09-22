# Busca a AMI mais recente do Ubuntu (Simulando 26.04 LTS ou a versão mais recente Noble/Jammy disponível)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    # Ubuntu 24.04 (Noble) é a LTS mais recente no momento, usando coringa para suportar futuras como 26.04
    values = ["ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_vpc" "default" {
  default = var.vpc_id == null ? true : false
  id      = var.vpc_id
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "app_sg" {
  name_prefix = "${var.project_name}-${var.environment}-sg"
  description = "Security Group para a aplicacao Acoes no Bolso rodando no Docker"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Aplicacao Web"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-sg"
    Environment = var.environment
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id != null ? var.subnet_id : data.aws_subnets.default.ids[0]

  vpc_security_group_ids = [aws_security_group.app_sg.id]
  
  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    github_repo_url            = var.github_repo_url
    env_file_content           = var.env_file_content
    google_credentials_content = var.google_credentials_content
  })
  user_data_replace_on_change = true

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

