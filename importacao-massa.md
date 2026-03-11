# Guia de Importação em Massa de Funcionários

Este documento descreve como utilizar os scripts de automação para importar funcionários e setores para o Sistema de Controle de Frequência a partir de arquivos Excel.

## Pré-requisitos

Certifique-se de que as dependências do projeto estejam instaladas:

```bash
pip install -r requirements.txt
```

---

## Passo 1: Gerar o Modelo de Importação

Antes de importar, você precisa de um arquivo Excel no formato correto. O sistema possui um script que gera esse modelo vazio com um exemplo:

**Comando:**
```bash
python3 src/gerar_modelo_excel.py
```

**Resultado:**
Será criado o arquivo `src/static/modelo_importacao.xlsx`.

---

## Passo 2: Preencher os Dados

Abra o arquivo `src/static/modelo_importacao.xlsx` e preencha as colunas conforme as orientações abaixo:

*   **SETOR:** Nome completo do setor (Ex: DIVISÃO DE ENFERMAGEM).
*   **SIGLA:** Sigla do setor (Ex: DIENF).
*   **LOTAÇÃO:** Localização específica ou subsetor.
*   **SIAPE:** Matrícula SIAPE do funcionário (única).
*   **NOME:** Nome completo do servidor.
*   **JORNADA:** Carga horária (Ex: 40H, 30H).
*   **ESCALA:** Tipo de escala (Ex: DIÁRIA, PLANTÃO).
*   **REMOTO_INT:** Se faz trabalho remoto integral (SIM/NÃO).
*   **REMOTO_REV:** Dias de revezamento, se houver (Ex: SEG, TER).
*   **CHEFIA_NOME:** Nome do chefe imediato do setor.
*   **CHEFIA_MATRICULA:** Matrícula da chefia.

> **Nota:** O script identifica o setor pelo nome. Se o setor já existir no banco de dados, o funcionário será vinculado a ele. Se não existir, o setor será criado automaticamente com os dados de Sigla e Chefia fornecidos na linha.

---

## Passo 3: Executar a Importação

Após salvar o arquivo preenchido, execute o script de importação apontando para o caminho do arquivo:

**Comando:**
```bash
python3 src/import_excel.py src/static/modelo_importacao.xlsx
```

**O que o script faz:**
1.  Valida se o arquivo existe.
2.  Lê linha por linha.
3.  Cria o setor se ele ainda não existir.
4.  Cria o funcionário se o SIAPE for novo.
5.  Ignora funcionários que já possuem o SIAPE cadastrado (evita duplicidade).
6.  Exibe um resumo ao final (Total de novos setores e novos funcionários).

---

## Dicas e Resolução de Problemas

*   **Erros de Importação:** Certifique-se de que não há linhas vazias no meio dos dados da planilha.
*   **Codificação:** O script utiliza a biblioteca `openpyxl` para garantir compatibilidade com arquivos `.xlsx` modernos.
*   **Auditoria:** Importações via script CLI são registradas diretamente no banco de dados. Para rastrear alterações futuras, utilize o painel "Logs de Auditoria" na interface web do gestor.
