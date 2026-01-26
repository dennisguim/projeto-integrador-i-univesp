import csv
import os
from app import app, db, Setor, Funcionario, Frequencia, Usuario

# Caminho para o CSV (assume que está na raiz do projeto, um nível acima de src)
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'planilha_de_frequencia.csv')

def import_data():
    if not os.path.exists(CSV_PATH):
        print(f"Erro: Arquivo não encontrado em {CSV_PATH}")
        return

    print("Iniciando importação...")
    
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

        # 1. Ler Cabeçalho (Linha 3 - índice 2) para pegar Mês, Ano (estimado) e Chefia
        # Ex: FREQUÊNCIA DO MÊS DE:,JANEIRO,,,CHEFIA: MÁRCIA CÉSAR ARAGÃO,MATRÍCULA:,3499580
        try:
            header_info = rows[2]
            mes_ref = header_info[1]
            chefia_nome_ref = header_info[5]
            chefia_matricula_ref = header_info[7]
            ano_ref = 2026 # Como não tem ano explícito na célula do mês, definimos aqui.
        except IndexError:
            print("Erro ao ler cabeçalho. Verifique o formato do CSV.")
            return

        # 2. Iterar dados (A partir da linha 5 - índice 4)
        count = 0
        for row in rows[4:]:
            # Verifica se a linha tem dados válidos (Setor não vazio)
            if len(row) < 2 or not row[1]: 
                continue

            # Mapeamento das colunas (índices baseados na lista gerada pelo CSV)
            # 0: (vazio), 1: SETOR, 2: SIGLA, 3: LOTAÇÃO, 4: SIAPE, 5: NOME, 
            # 6: JORNADA, 7: ESCALA, 8: REMOTO_INT, 9: REMOTO_REV, 10: FREQ_INT, 11: OBS
            
            nome_setor = row[1].strip()
            sigla = row[2].strip()
            lotacao = row[3].strip()
            siape = row[4].strip()
            nome_func = row[5].strip()
            jornada = row[6].strip()
            escala = row[7].strip()
            remoto_int = row[8].strip()
            remoto_rev = row[9].strip()
            freq_int = row[10].strip()
            obs = row[11].strip()

            # Lógica para evitar duplicar Setores
            # Verifica se já existe um setor com esse nome E lotação (pois lotação varia)
            setor = Setor.query.filter_by(nome=nome_setor, lotacao=lotacao).first()
            if not setor:
                setor = Setor(
                    nome=nome_setor,
                    sigla=sigla,
                    lotacao=lotacao,
                    chefia_nome=chefia_nome_ref,
                    chefia_matricula=chefia_matricula_ref
                )
                db.session.add(setor)
                db.session.commit() # Commita para gerar o ID

            # Lógica para Funcionário
            funcionario = Funcionario.query.filter_by(siape=siape).first()
            if not funcionario:
                funcionario = Funcionario(
                    nome=nome_func,
                    siape=siape,
                    jornada=jornada,
                    escala=escala,
                    trabalho_remoto_integral=remoto_int,
                    dias_remoto_revezamento=remoto_rev,
                    setor_id=setor.id
                )
                db.session.add(funcionario)
                db.session.commit()
            
            # Lógica para Frequência (Sempre cria uma nova para o mês)
            frequencia = Frequencia(
                mes=mes_ref,
                ano=ano_ref,
                frequencia_integral=freq_int,
                observacoes=obs,
                funcionario_id=funcionario.id
            )
            db.session.add(frequencia)
            count += 1
        
        # Criar Usuários de Teste
        if not Usuario.query.filter_by(nome_usuario='admin').first():
            admin = Usuario(nome_usuario='admin', senha='123', perfil='gestor')
            db.session.add(admin)
        
        if not Usuario.query.filter_by(nome_usuario='chefe').first():
            chefe = Usuario(nome_usuario='chefe', senha='123', perfil='chefe')
            db.session.add(chefe)

        db.session.commit()
        print(f"Sucesso! {count} registros de frequência importados.")
        print("Usuários criados: 'admin' (senha: 123) e 'chefe' (senha: 123)")

if __name__ == '__main__':
    with app.app_context():
        import_data()
