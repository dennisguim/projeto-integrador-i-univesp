import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template

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
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(80), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False) # Usar hash num projeto real
    perfil = db.Column(db.String(50), nullable=False) # Chefia ou Consolidador

    def __repr__(self):
        return f'<Usuario {self.nome_usuario}>'

class Ocorrencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)

    # cria a relacao com a tabela Usuario (chave estrangeira)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    # Acessar o objeto Usuario a partir de uma Ocorrencia
    usuario = db.relationship('Usuario', backref=db.backref('ocorrencias', lazy=True))

    def __repr__(self):
        return f'<Ocorrencia {self.descricao}>'
    
# ---- ROTAS (PÁGINAS) ----
@app.route('/')
def index():
    # render_template busca e processa o arquivo html da pasta templates
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)