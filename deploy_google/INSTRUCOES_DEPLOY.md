# Instruções para Deploy no Google Cloud Run

Este guia explica como preparar e enviar o sistema para a infraestrutura do Google Cloud.

## 1. Preparação da Chave Privada
Se você for usar a conta de um colega, você precisará:
1.  Gerar uma nova chave JSON no Firebase dele (conforme o Passo 1).
2.  Substituir o arquivo `google-credentials.json` na raiz do projeto pela nova chave.
3.  **No código (`src/app.py`)**: O sistema já está configurado para procurar o arquivo pelo nome `google-credentials.json`. Se você mantiver este nome, **não precisa alterar o código**.

## 2. O Dockerfile
O arquivo `Dockerfile` na pasta `deploy_google/` é o que o Google usa para criar o servidor. Você pode editá-lo a qualquer momento antes do deploy. Ele instala o Python, as dependências e define como o site inicia.

## 3. Passo a Passo do Deploy
Com o [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) instalado no seu computador, execute:

```bash
# 1. Login na conta do colega
gcloud auth login

# 2. Selecionar o projeto dele
gcloud config set project ID_DO_PROJETO_DELE

# 3. Executar o Deploy (Rode este comando na raiz do projeto)
gcloud run deploy sistema-frequencia \
  --source . \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated
```

## 4. O que alterar se mudar de conta?
*   **google-credentials.json**: Substitua o arquivo físico.
*   **Variáveis de Ambiente**: Se quiser ser mais profissional, pode configurar o `SECRET_KEY` diretamente no painel do Cloud Run em vez de deixar no código.

---
*Nota: O Dockerfile que criei já considera que seu código está na pasta `src/`.*
