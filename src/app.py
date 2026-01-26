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

'''    def __repr__(self):
        return f'<Usuario {self.nome_usuario}>'''

class Setor(db.Model):
    # Setores listados na planilha
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sigla = db.Column(db.String(50))
    lotacao = db.Column(db.String(100))
    chefia_nome = db.Column(db.String(100))
    chefia_matricula = db.Column(db.String(50))

    #relacionamento com funcionario
    funcionarios = db.relationship('Funcionario', backref='setor', lazy=True)

class Funcionario(db.Model):
    # Dados cadastrais do funcionario
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    siape = db.Column(db.String(20), unique=True, nullable=False)
    jornada = db.Column(db.String(50))
    escala = db.Column(db.String(100))
    trabalho_remoto_integral = db.Column(db.String(10))
    dias_remoto_revezamento = db.Column(db.String(50))

    setor_id = db.Column(db.Integer, db.ForeignKey('setor.id'), nullable=False)

    # Relacionamento com Frequencia
    frequencias = db.relationship('Frequencia', backref='funcionario', lazy=True)

class Frequencia(db.Model):
    # Registro mensal de frequência
    id = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.String(20), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    frequencia_integral = db.Column(db.String(10))
    observacoes = db.Column(db.Text)

    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)

# ---- ROTAS (PÁGINAS) ----
@app.route('/')
def index():
    # render_template busca e processa o arquivo html da pasta templates
    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)