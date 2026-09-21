FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY pyproject.toml ./

# Instalar o pacote
RUN pip install --no-cache-dir pip setuptools wheel
COPY src/ src/
COPY static/ static/
RUN pip install --no-cache-dir .

# Expor a porta que o FastAPI/Dash vai rodar
EXPOSE 8000

# Variáveis de ambiente padrão
ENV DASH_HOST=0.0.0.0
ENV DASH_PORT=8000

# Comando para rodar a aplicação
CMD ["acoes-api"]

