import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configurações do banco de dados
#Necessário para login e sessão
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura'
# Define o caminho para o arquivo database.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
# Desativar rastreamneto de mod para economizar recursos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instancia do bd
db = SQLAlchemy(app)

# config do flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # nome da função da rota de login

# carregar usuário
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- MODELOS (Tabelas) ----
class Usuario(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(80), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False) # Usar hash num projeto real
    perfil = db.Column(db.String(50), nullable=False) # Chefia ou Consolidador

    def __repr__(self):
        return f'<Usuario {self.nome_usuario}>'

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
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Usuario.query.filter_by(nome_usuario=username).first()

        # Verificação de senha (posteriormente usar hash)
        if user and user.senha == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required # só entra logado
def dashboard():
    # render_template busca e processa o arquivo html da pasta templates
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)