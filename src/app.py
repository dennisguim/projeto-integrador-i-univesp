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
    # adicionado
    setor_id = db.Column(db.Integer, db.ForeignKey('setor.id'), nullable=True)

    setor_vinculado = db.relationship('Setor', backref='usuarios_gestores')

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

@app.route('/funcionarios')
@login_required
def listar_funcionarios():
    # se for chefe, ve apenas o setor, se for gestor ve tudo
    if current_user.perfil == 'chefe' and current_user.setor_id:
        lista = Funcionario.query.filter_by(setor_id=current_user.setor_id).all()
    else:
    # Busca todos os funcionários
        lista = Funcionario.query.all()

    return render_template('lista_funcionarios.html', funcionarios=lista)

@app.route('/funcionarios/frequencia/<int:func_id>', methods=['GET', 'POST'])
@login_required
def registrar_frequencia(func_id):
    funcionario = Funcionario.query.get_or_404(func_id)

    # verificacao de seguranca. chefe só lança para o seu setor
    if current_user.perfil == 'chefe' and funcionario.setor_id != current_user.setor_id:
        flash('Acesso negado: Este funcionário não pertence ao seu setor.')
        return redirect(url_for('listar_funcionarios'))
    
    if request.method == 'POST':
        mes = request.form.get('mes')
        ano = request.form.get('ano')
        freq_int = request.form.get('frequencia_integral')
        obs = request.form.get('observacoes')

        # cria registro de frequencia
        nova_freq = Frequencia(
            mes=mes,
            ano=int(ano),
            frequencia_integral=freq_int,
            observacoes=obs,
            funcionario_id=funcionario.id
        )
        db.session.add(nova_freq)
        db.session.commit()

        flash(f'Frequência de {funcionario.nome} ({mes}/{ano}) registrada!')
        return redirect(url_for('listar_funcionarios'))
    
    return render_template('registrar_frequencia.html', funcionario=funcionario)

@app.route('/funcionarios/novo', methods=['GET', 'POST'])
@login_required
def novo_funcionario():
    # Apenas o gestor pode cadastrar
    if current_user.perfil != 'gestor':
        flash('Acesso negado: Apenas gestores podem cadastrar funcionários.')
        return redirect(url_for('listar_funcionarios'))
    
    if request.method == 'POST':
        # Captura dados do formulário
        nome = request.form.get('nome').upper()
        siape = request.form.get('siape')
        setor_id = request.form.get('setor_id')
        jornada = request.form.get('jornada')
        escala = request.form.get('escala')
        remoto_integral = request.form.get('remoto_integral')

        # salva no banco
        novo = Funcionario(
            nome=nome,
            siape=siape,
            setor_id=int(setor_id),
            jornada=jornada,
            escala=escala,
            trabalho_remoto_integral=remoto_integral,
            dias_remoto_revezamento="NÃO" # padrão inicial
        )
        db.session.add(novo)
        db.session.commit()

        flash(f'Funcionário {nome} cadastrado com sucesso!')
        return redirect(url_for('listar_funcionarios'))
    
    # Sefor GET, mostra o formulário (precisa dos setores para o <select>)
    setores = Setor.query.all()
    return render_template('form_funcionario.html', setores=setores)

@app.route('/relatorio', methods=['GET', 'POST'])
@login_required
def relatorio_geral():
    # Apenas o gestor pode ver o relatório geral
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    
    # Valores Padrão
    mes_filtro = 'JANEIRO'
    ano_filtro = 2026
    resultados = []

    if request.method == 'POST':
        mes_filtro = request.form.get('mes')
        ano_filtro = int(request.form.get('ano'))

        # busca frequencias filtradas por ano e mes
        # join com funcionario e setor para exibir os dados completos
        resultados = Frequencia.query\
            .join(Funcionario)\
            .join(Setor)\
            .filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)\
            .all()
    
    return render_template('relatorio.html',
                           registros=resultados,
                           mes_atual=mes_filtro,
                           ano_atual=ano_filtro)

@app.route('/funcionarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_funcionario(id):
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        returnredirect(url_for('listar_funcionarios'))
    
    func = Funcionario.query.get_or_404(id)

    if request.method == 'POST':
        func.nome = request.form.get('nome').upper()
        func.siape = request.form.get('siape')
        func.setor_id = int(request.form.get('setor_id'))
        func.jornada = request.form.get('jornada')
        func.escala = request.form.get('escala')
        func.trabalho_remoto_integral = request.form.get('remoto_integral')

        db.session.commit()
        flash(f'Dados de {func.nome} atualizados!')
        return redirect(url_for('listar_funcionarios'))
    
    setores = Setor.query.all()
    return render_template('form_funcionario.html', setores=setores, funcionario=func)

@app.route('/funcionarios/excluir/<int:id>')
@login_required
def excluir_funcionario(id):
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('listar_funcionarios'))
    
    func = Funcionario.query.get_or_404(id)
    nome = func.nome

    # remove as frequencias antes de excluir para evitar erro no bd
    Frequencia.query.filter_by(funcionario_id=id).delete()

    db.session.delete(func)
    db.session.commit()

    flash(f'Funcionário {nome} removido do sistema.')
    return redirect(url_for('listar_funcionarios'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)