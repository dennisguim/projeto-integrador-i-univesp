# Sistema de Controle de Frequência - INCA HCIII

Este projeto é uma solução web desenvolvida para automatizar e padronizar o processo de consolidação da frequência mensal dos servidores da Divisão de Enfermagem do **Hospital do Câncer III (HCIII)** do **Instituto Nacional de Câncer (INCA)**.

O objetivo principal é substituir o processo manual fragmentado de 10 setores distintos por um sistema centralizado que gere relatórios automáticos conforme as exigências do RH.

---

## Funcionalidades Principais

- **Autenticação e Controle de Acesso (RBAC):**
  - **Perfil Gestor:** Visão sistêmica, cadastro de setores/funcionários e geração do relatório mestre consolidado.
  - **Perfil Chefe de Setor:** Gerenciamento exclusivo da equipe de sua unidade (registro de faltas, licenças, capacitações).
- **Gestão de Servidores:** Cadastro completo incluindo SIAPE, jornada, escala e regime de trabalho (presencial ou remoto).
- **Registro de Ocorrências:** Lançamento ágil de eventos de frequência ao longo do mês.
- **Consolidação Automática:** Geração instantânea do relatório mensal em formato padronizado, eliminando o retrabalho manual de unir subplanilhas.
- **Auditoria Basica:** Registro de quem realizou as alterações para maior transparência.

---

## Tecnologias Utilizadas

- **Backend:** [Python](https://www.python.org/) com o framework [Flask](https://flask.palletsprojects.com/)
- **Banco de Dados:** [SQLite](https://www.sqlite.org/) (Relacional, leve e portátil)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) para abstração de banco de dados
- **Frontend:** HTML5, CSS3 e Jinja2 (Templates dinâmicos)
- **Autenticação:** Flask-Login para gerenciamento de sessões seguras

---

## Estrutura do Projeto

```text
projeto/
├── src/
│   ├── app.py              # Ponto de entrada da aplicação Flask
│   ├── database.db         # Arquivo do banco de dados SQLite
│   ├── static/             # Arquivos CSS, JS e Imagens
│   └── templates/          # Arquivos HTML (Jinja2)
├── requirements.txt        # Dependências do projeto
├── README.md               # Documentação principal
└── documentacao_tecnica.md # Detalhamento da arquitetura e UML
```

---

## Como Executar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd pji110-projeto-integrador-em-computacao-i/projeto
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # No Windows: .venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a aplicação:**
   ```bash
   python src/app.py
   ```

5. **Acesse no navegador:**
   `http://127.0.0.1:5000`

---

## Contexto Acadêmico

Este sistema foi desenvolvido como parte do **Projeto Integrador em Computação I** do curso de Ciência de Dados da **Univesp (Universidade Virtual do Estado de São Paulo)**.

O projeto aplica conhecimentos práticos de:
- Engenharia de Software (Diagramas UML)
- Desenvolvimento Web (Backend e Frontend)
- Modelagem de Bancos de Dados Relacionais
- Gestão de Processos e Transformação Digital em Instituições Públicas

---

## Licença

Este projeto é de caráter acadêmico e destinado ao uso interno na Divisão de Enfermagem do INCA HCIII.
