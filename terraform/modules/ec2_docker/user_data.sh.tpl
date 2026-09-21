#!/bin/bash
set -e

# Atualiza pacotes e instala dependências básicas
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg lsb-release git

# Instala Docker Oficial para Ubuntu
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adiciona o usuário ubuntu ao grupo docker
usermod -aG docker ubuntu

# Configura o Docker para iniciar no boot
systemctl enable docker
systemctl start docker

# ==========================================
# Script de inicialização da Aplicação
# ==========================================
cd /home/ubuntu
git clone ${github_repo_url}
# Entra na pasta clonada (pega o nome do repositório a partir da URL)
REPO_DIR=$(basename ${github_repo_url} .git)
cd $REPO_DIR

# Cria o arquivo .env com o conteúdo passado via Terraform
cat << 'EOF' > .env
${env_file_content}
EOF

# Garante a porta correta no .env do docker
sed -i 's/DASH_HOST=.*/DASH_HOST=0.0.0.0/g' .env
sed -i 's/DASH_PORT=.*/DASH_PORT=8000/g' .env

# Cria o arquivo JSON do Google
mkdir -p credentials
cat << 'EOF' > credentials/service-account.json
${google_credentials_content}
EOF

# Build da Imagem
docker build -t acoes-api .

# Run
docker run -d -p 8000:8000 --name acoes_app --restart always --env-file .env -v $(pwd)/credentials:/app/credentials acoes-api
