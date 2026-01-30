import os
import io
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
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
    chefia_nome = db.Column(db.String(100))
    chefia_matricula = db.Column(db.String(50))

    #relacionamento com funcionario
    funcionarios = db.relationship('Funcionario', backref='setor', lazy=True)

class Funcionario(db.Model):
    # Dados cadastrais do funcionario
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    siape = db.Column(db.String(20), unique=True, nullable=False)
    lotacao = db.Column(db.String(100))
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
            lotacao=request.form.get('lotacao'),
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

@app.route('/relatorio', methods=['GET'])
@login_required
def relatorio_geral():
    # Apenas gestor pode ver relatório geral
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))

    # Valores padrão para filtros (agora via GET)
    mes_filtro = request.args.get('mes', 'JANEIRO')
    ano_filtro = request.args.get('ano', 2026, type=int)
    setor_id = request.args.get('setor_id', type=int)
    nome_busca = request.args.get('nome', '').strip()
    freq_integral_filtro = request.args.get('freq_integral', '')

    # Query Base (Filtro de tempo é obrigatório)
    query = Frequencia.query\
        .join(Funcionario)\
        .join(Setor)\
        .filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)
    
    # Filtros Adicionais (Opcionais)
    if setor_id:
        query = query.filter(Funcionario.setor_id == setor_id)
    
    if nome_busca:
        # Filtra por Nome ou SIAPE
        query = query.filter(
            (Funcionario.nome.contains(nome_busca.upper())) | 
            (Funcionario.siape.contains(nome_busca))
        )
    
    if freq_integral_filtro:
        query = query.filter(Frequencia.frequencia_integral == freq_integral_filtro)

    resultados = query.all()
    setores = Setor.query.order_by(Setor.nome).all()

    # Passamos os filtros atuais para manter o formulário preenchido
    filtros_atuais = {
        'mes': mes_filtro,
        'ano': ano_filtro,
        'setor_id': setor_id,
        'nome': nome_busca,
        'freq_integral': freq_integral_filtro
    }

    return render_template('relatorio.html', 
                           registros=resultados, 
                           setores=setores,
                           filtros=filtros_atuais)

@app.route('/funcionarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_funcionario(id):
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('listar_funcionarios'))
    
    func = Funcionario.query.get_or_404(id)

    if request.method == 'POST':
        func.nome = request.form.get('nome').upper()
        func.siape = request.form.get('siape')
        func.lotacao = request.form.get('lotacao')
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

@app.route('/relatorio/exportar')
@login_required
def exportar_relatorio():
    if current_user.perfil != 'gestor':
        return redirect(url_for('dashboard'))

    # Recupera os mesmos filtros da URL (request.args)
    mes_filtro = request.args.get('mes')
    ano_filtro = request.args.get('ano', type=int)
    setor_id = request.args.get('setor_id', type=int)
    nome_busca = request.args.get('nome', '').strip()
    freq_integral_filtro = request.args.get('freq_integral', '')

    query = Frequencia.query\
        .join(Funcionario)\
        .join(Setor)\
        .filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)

    if setor_id:
        query = query.filter(Funcionario.setor_id == setor_id)
    if nome_busca:
        query = query.filter(
            (Funcionario.nome.contains(nome_busca.upper())) | 
            (Funcionario.siape.contains(nome_busca))
        )
    if freq_integral_filtro:
        query = query.filter(Frequencia.frequencia_integral == freq_integral_filtro)

    resultados = query.all()

    # Criação do CSV em memória
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';') 
    
    # Cabeçalho
    cw.writerow(['SETOR', 'SIGLA', 'LOTAÇÃO', 'SERVIDOR', 'SIAPE', 'REMOTO (REV)', 'FREQ. INTEGRAL', 'OBSERVAÇÕES'])
    
    # Dados
    for freq in resultados:
        cw.writerow([
            freq.funcionario.setor.nome,
            freq.funcionario.setor.sigla,
            freq.funcionario.lotacao,
            freq.funcionario.nome,
            freq.funcionario.siape,
            freq.funcionario.dias_remoto_revezamento,
            freq.frequencia_integral,
            freq.observacoes
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=frequencia_{mes_filtro}_{ano_filtro}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/setores')
@login_required
def listar_setores():
    if current_user.perfil != 'gestor': return redirect(url_for('dashboard'))
    lista = Setor.query.all()
    return render_template('lista_setores.html', setores=lista)

@app.route('/setores/novo', methods={'GET', 'POST'})
@login_required
def novo_setor():
    if current_user.perfil != 'gestor': return redirect(url_for('dashboard'))

    if request.method == 'POST':
        novo = Setor(
            nome=request.form.get('nome'),
            sigla=request.form.get('sigla'),   
            chefia_nome=request.form.get('chefia_nome'),
            chefia_matricula=request.form.get('chefia_matricula')
        )
        db.session.add(novo)
        db.session.commit()
        flash('Setor criado!')
        return redirect(url_for('listar_setores'))
    
    return render_template('form_setor.html')

@app.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if current_user.perfil != 'gestor': return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        novo_user = Usuario(
            nome_usuario=request.form.get('username'),
            senha=request.form.get('password'),
            perfil=request.form.get('perfil'),
            setor_id=request.form.get('setor_id') if request.form.get('setor_id') else None
        )
        db.session.add(novo_user)
        db.session.commit()
        flash('Usuário criado com sucesso!')
        return redirect(url_for('dashboard'))
        
    setores = Setor.query.all()
    return render_template('form_usuario.html', setores=setores)

@app.route('/setores/excluir/<int:id>')
@login_required
def excluir_setor(id):
    if current_user.perfil != 'gestor': return redirect(url_for('dashboard'))
    
    setor = Setor.query.get_or_404(id)
    
    # Verifica se tem funcionários
    if setor.funcionarios:
        flash('Erro: Não é possível excluir um setor que possui funcionários vinculados.')
    else:
        db.session.delete(setor)
        db.session.commit()
        flash(f'Setor {setor.nome} excluído.')
        
    return redirect(url_for('listar_setores'))

@app.route('/usuarios')
@login_required
def listar_usuarios():
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    
    lista = Usuario.query.all()
    return render_template('lista_usuarios.html', usuarios=lista)

@app.route('/usuarios/excluir/<int:id>')
@login_required
def excluir_usuario(id):
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    
    if id == current_user.id:
        flash('Erro: Você não pode excluir seu próprio usuário.')
        return redirect(url_for('listar_usuarios'))

    user = Usuario.query.get_or_404(id)
    nome = user.nome_usuario
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuário {nome} excluído com sucesso.')
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios/alterar_senha/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_alterar_senha(id):
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))

    user = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        if nova_senha:
            user.senha = nova_senha # Em produção usar hash
            db.session.commit()
            flash(f'Senha de {user.nome_usuario} alterada com sucesso!')
            return redirect(url_for('listar_usuarios'))
        else:
            flash('A senha não pode ser vazia.')

    return render_template('alterar_senha.html', usuario=user)

@app.route('/minha_conta/alterar_senha', methods=['GET', 'POST'])
@login_required
def minha_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar = request.form.get('confirmar_senha')

        if current_user.senha != senha_atual:
            flash('Senha atual incorreta.')
        elif nova_senha != confirmar:
            flash('A nova senha e a confirmação não coincidem.')
        elif not nova_senha:
             flash('A nova senha não pode ser vazia.')
        else:
            current_user.senha = nova_senha
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!')
            return redirect(url_for('dashboard'))
            
    return render_template('minha_senha.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)