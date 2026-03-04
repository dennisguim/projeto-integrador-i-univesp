import os
import io
import csv
import tempfile
import openpyxl
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Importações para Google API
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configurações do Google API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Apenas para desenvolvimento local (HTTP)
CLIENT_SECRETS_FILE = os.path.join(os.path.abspath(os.path.join(basedir, os.pardir)), 'client_secret.json')

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
    lotacao = db.Column(db.String(100)) # Adicionado
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

@app.route('/funcionarios', methods=['GET'])
@login_required
def listar_funcionarios():
    # Parâmetros de Filtro (Mês/Ano referência para saber quem já lançou)
    mes_ref = request.args.get('mes', 'JANEIRO')
    ano_ref = request.args.get('ano', 2026, type=int)

    # 1. Buscar todos os funcionários acessíveis ao usuário
    if current_user.perfil == 'chefe' and current_user.setor_id:
        todos_funcionarios = Funcionario.query.filter_by(setor_id=current_user.setor_id).order_by(Funcionario.nome).all()
    else:
        todos_funcionarios = Funcionario.query.order_by(Funcionario.nome).all()

    # 2. Separar em duas listas: Pendentes e Concluídos
    pendentes = []
    concluidos = []

    for func in todos_funcionarios:
        # Verifica se existe frequência para este funcionário no mês/ano selecionado
        freq = Frequencia.query.filter_by(
            funcionario_id=func.id,
            mes=mes_ref,
            ano=ano_ref
        ).first()

        if freq:
            # Adiciona um atributo temporário para exibir no template se necessário
            func.freq_registrada = freq 
            concluidos.append(func)
        else:
            pendentes.append(func)

    return render_template('lista_funcionarios.html', 
                           pendentes=pendentes, 
                           concluidos=concluidos,
                           mes_ref=mes_ref,
                           ano_ref=ano_ref)

@app.route('/funcionarios/frequencia/<int:func_id>', methods=['GET', 'POST'])
@login_required
def registrar_frequencia(func_id):
    funcionario = Funcionario.query.get_or_404(func_id)

    # verificacao de seguranca. chefe só lança para o seu setor
    if current_user.perfil == 'chefe' and funcionario.setor_id != current_user.setor_id:
        flash('Acesso negado: Este funcionário não pertence ao seu setor.')
        return redirect(url_for('listar_funcionarios'))
    
    # Se receber via GET (clique no botão da lista), preenchemos o formulário
    mes_selecionado = request.args.get('mes')
    ano_selecionado = request.args.get('ano')
    
    if request.method == 'POST':
        mes = request.form.get('mes')
        ano = request.form.get('ano')
        freq_int = request.form.get('frequencia_integral')
        obs = request.form.get('observacoes')

        # Verifica se já existe (Evitar duplicidade manual)
        existente = Frequencia.query.filter_by(
            funcionario_id=funcionario.id,
            mes=mes,
            ano=int(ano)
        ).first()

        if existente:
             # Atualiza em vez de criar novo (ou avisa erro, dependendo da regra. Aqui vou atualizar)
             existente.frequencia_integral = freq_int
             existente.observacoes = obs
             flash(f'Frequência de {funcionario.nome} ({mes}/{ano}) atualizada!')
        else:
            # cria registro de frequencia
            nova_freq = Frequencia(
                mes=mes,
                ano=int(ano),
                frequencia_integral=freq_int,
                observacoes=obs,
                funcionario_id=funcionario.id
            )
            db.session.add(nova_freq)
            flash(f'Frequência de {funcionario.nome} ({mes}/{ano}) registrada!')
            
        db.session.commit()

        # Retorna para a lista mantendo o filtro de mês/ano
        return redirect(url_for('listar_funcionarios', mes=mes, ano=ano))
    
    return render_template('registrar_frequencia.html', 
                           funcionario=funcionario,
                           mes_padrao=mes_selecionado,
                           ano_padrao=ano_selecionado)

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
    
    # Remove as frequências vinculadas antes de excluir o funcionário
    Frequencia.query.filter_by(funcionario_id=id).delete()
    
    db.session.delete(func)
    db.session.commit()
    
    flash(f'Funcionário {nome} removido do sistema.')
    return redirect(url_for('listar_funcionarios'))

@app.route('/relatorio', methods=['GET'])
@login_required
def relatorio_geral():
    # Apenas gestor pode ver relatório geral
    if current_user.perfil != 'gestor':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))

    # Valores padrão para filtros
    mes_filtro = request.args.get('mes', 'JANEIRO')
    ano_filtro = request.args.get('ano', 2026, type=int)
    setor_id = request.args.get('setor_id', type=int)
    nome_busca = request.args.get('nome', '').strip()
    freq_integral_filtro = request.args.get('freq_integral', '')

    # Query Base
    query = Frequencia.query\
        .join(Funcionario)\
        .join(Setor)\
        .filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)
    
    # Filtros Adicionais
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

@app.route('/relatorio/exportar')
@login_required
def exportar_relatorio():
    if current_user.perfil != 'gestor':
        return redirect(url_for('dashboard'))

    # 1. Recuperar dados filtrados
    mes_filtro = request.args.get('mes')
    ano_filtro = request.args.get('ano', type=int)
    setor_id = request.args.get('setor_id', type=int)
    nome_busca = request.args.get('nome', '').strip()
    freq_integral_filtro = request.args.get('freq_integral', '')

    query = Frequencia.query.join(Funcionario).join(Setor).filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)
    if setor_id: query = query.filter(Funcionario.setor_id == setor_id)
    if nome_busca: query = query.filter((Funcionario.nome.contains(nome_busca.upper())) | (Funcionario.siape.contains(nome_busca)))
    if freq_integral_filtro: query = query.filter(Frequencia.frequencia_integral == freq_integral_filtro)

    resultados = query.all()

    # 2. Manipular Excel com Modelo Local
    caminho_modelo = os.path.join(app.static_folder, 'modelo_frequencia.xlsx')
    wb = openpyxl.load_workbook(caminho_modelo)
    ws = wb.active

    # Ajuste de linhas se necessário
    num_registros = len(resultados)
    if num_registros > 188:
        ws.insert_rows(193, num_registros - 188)

    # Preencher dados (B=2 até L=12)
    # Ordem: SETOR;SIGLA;LOTAÇÃO;SIAPE;NOME;JORNADA;ESCALA;REMOTO_INT;REMOTO_REV;FREQ_INT;OBS
    for i, freq in enumerate(resultados):
        row = 5 + i
        ws.cell(row=row, column=2).value = freq.funcionario.setor.nome
        ws.cell(row=row, column=3).value = freq.funcionario.setor.sigla
        ws.cell(row=row, column=4).value = freq.funcionario.lotacao
        ws.cell(row=row, column=5).value = freq.funcionario.siape
        ws.cell(row=row, column=6).value = freq.funcionario.nome
        ws.cell(row=row, column=7).value = freq.funcionario.jornada
        ws.cell(row=row, column=8).value = freq.funcionario.escala
        ws.cell(row=row, column=9).value = freq.funcionario.trabalho_remoto_integral
        ws.cell(row=row, column=10).value = freq.funcionario.dias_remoto_revezamento
        ws.cell(row=row, column=11).value = freq.frequencia_integral
        ws.cell(row=row, column=12).value = freq.observacoes

    # 3. Retornar Excel
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename=frequencia_{mes_filtro}_{ano_filtro}.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

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

@app.route('/setores')
@login_required
def listar_setores():
    if current_user.perfil != 'gestor': return redirect(url_for('dashboard'))
    lista = Setor.query.all()
    return render_template('lista_setores.html', setores=lista)

@app.route('/setores/novo', methods=['GET', 'POST'])
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
        return redirect(url_for('listar_usuarios'))
        
    setores = Setor.query.all()
    return render_template('form_usuario.html', setores=setores)

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

@app.route('/google/login')
@login_required
def google_login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        flash("Arquivo 'client_secret.json' não encontrado na raiz do projeto. Verifique o guia 'google-planilhas.md'.")
        return redirect(url_for('relatorio_geral'))

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('google_callback', _external=True)
    
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    session['google_filters'] = request.args.to_dict()
    
    return redirect(authorization_url)

@app.route('/google/callback')
def google_callback():
    state = session.get('state')
    if not state:
        return redirect(url_for('relatorio_geral'))

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('google_callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['google_credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    filtros = session.get('google_filters', {})
    return redirect(url_for('exportar_google_sheets', **filtros))

@app.route('/relatorio/google-sheets')
@login_required
def exportar_google_sheets():
    if 'google_credentials' not in session:
        return redirect(url_for('google_login', **request.args))

    # 1. Recuperar dados filtrados
    mes_filtro = request.args.get('mes')
    ano_filtro = request.args.get('ano', type=int)
    setor_id = request.args.get('setor_id', type=int)
    nome_busca = request.args.get('nome', '').strip()
    freq_integral_filtro = request.args.get('freq_integral', '')

    query = Frequencia.query.join(Funcionario).join(Setor).filter(Frequencia.mes == mes_filtro, Frequencia.ano == ano_filtro)
    if setor_id: query = query.filter(Funcionario.setor_id == setor_id)
    if nome_busca: query = query.filter((Funcionario.nome.contains(nome_busca.upper())) | (Funcionario.siape.contains(nome_busca)))
    if freq_integral_filtro: query = query.filter(Frequencia.frequencia_integral == freq_integral_filtro)

    resultados = query.all()

    if not resultados:
        flash("Nenhum registro encontrado para exportar.")
        return redirect(url_for('relatorio_geral', **request.args))

    # 2. Manipular Excel com Modelo Local
    caminho_modelo = os.path.join(app.static_folder, 'modelo_frequencia.xlsx')
    if not os.path.exists(caminho_modelo):
        flash(f"Modelo Excel não encontrado em {caminho_modelo}")
        return redirect(url_for('relatorio_geral', **request.args))

    wb = openpyxl.load_workbook(caminho_modelo)
    ws = wb.active

    # Se houver mais de 188 registros (5 a 192), insere linhas extras mantendo as instruções
    num_registros = len(resultados)
    limite_padrao = 188
    if num_registros > limite_padrao:
        linhas_extras = num_registros - limite_padrao
        ws.insert_rows(193, linhas_extras) # Insere a partir da 193 (antes das instruções)

    # Preencher dados (B=2 até L=12)
    # Ordem: SETOR;SIGLA;LOTAÇÃO;SIAPE;NOME;JORNADA;ESCALA;REMOTO_INT;REMOTO_REV;FREQ_INT;OBS
    for i, freq in enumerate(resultados):
        row = 5 + i
        ws.cell(row=row, column=2).value = freq.funcionario.setor.nome
        ws.cell(row=row, column=3).value = freq.funcionario.setor.sigla
        ws.cell(row=row, column=4).value = freq.funcionario.lotacao
        ws.cell(row=row, column=5).value = freq.funcionario.siape
        ws.cell(row=row, column=6).value = freq.funcionario.nome
        ws.cell(row=row, column=7).value = freq.funcionario.jornada
        ws.cell(row=row, column=8).value = freq.funcionario.escala
        ws.cell(row=row, column=9).value = freq.funcionario.trabalho_remoto_integral
        ws.cell(row=row, column=10).value = freq.funcionario.dias_remoto_revezamento
        ws.cell(row=row, column=11).value = freq.frequencia_integral
        ws.cell(row=row, column=12).value = freq.observacoes

    # Salva em arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        temp_path = tmp.name
        wb.save(temp_path)

    # 3. Upload e Conversão para Google Sheets
    try:
        creds = google.oauth2.credentials.Credentials(**session['google_credentials'])
        # Build Drive service to upload file
        drive_service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': f'Relatório Frequência {mes_filtro}-{ano_filtro}',
            'mimeType': 'application/vnd.google-apps.spreadsheet' # Conversão automática
        }
        media = MediaFileUpload(temp_path, 
                                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                resumable=True)
        
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        flash(f'Sucesso! Planilha criada no seu Google Drive (ID: {file.get("id")})')
    except Exception as e:
        flash(f'Erro ao salvar no Google Drive: {str(e)}')
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return redirect(url_for('relatorio_geral', **request.args))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)