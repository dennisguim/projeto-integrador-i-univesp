# Usar uma imagem oficial do Python
FROM python:3.12-slim

# Evitar que o Python gere arquivos .pyc e permitir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias (opcional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de requisitos primeiro (melhora o cache do Docker)
COPY requirements.txt .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do projeto
COPY . .

# O Cloud Run define a porta via variável de ambiente PORT (padrão 8080)
ENV PORT 8080

# Comando para iniciar o servidor usando Gunicorn (mais robusto que o Flask run)
# 'src.app:app' diz para procurar o objeto 'app' dentro de 'src/app.py'
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 src.app:app
