import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configurações do banco de dados
# Define o caminho para o arquivo database.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
# Desativar rastreamneto de mod para economizar recursos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instancia do bd
db = SQLAlchemy(app)

# --- MODELOS (Tabelas) ----

# ---- ROTAS (PÁGINAS) ----
@app.route('/')
def hello_world():
    return 'Projeto no ar com o banco de dados configurado'

if __name__ == '__main__':
    app.run(debug=True)
    