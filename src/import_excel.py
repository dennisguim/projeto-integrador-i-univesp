import openpyxl
import os
import sys

# Adiciona o diretório atual ao sys.path para importar app e db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Setor, Funcionario, registrar_log

def import_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return

    print(f"Lendo arquivo: {file_path}")
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    # Espera que o cabeçalho esteja na linha 1
    # Colunas: 
    # 1: SETOR, 2: SIGLA, 3: LOTAÇÃO, 4: SIAPE, 5: NOME, 
    # 6: JORNADA, 7: ESCALA, 8: REMOTO_INT, 9: REMOTO_REV,
    # 10: CHEFIA_NOME, 11: CHEFIA_MATRICULA

    count_setores = 0
    count_funcs = 0

    # Iterar a partir da linha 2
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] or not row[4]: # Pula se o setor ou nome do funcionário estiver vazio
            continue

        nome_setor = str(row[0]).strip().upper()
        sigla = str(row[1]).strip().upper() if row[1] else ""
        lotacao = str(row[2]).strip().upper() if row[2] else ""
        siape = str(row[3]).strip()
        nome_func = str(row[4]).strip().upper()
        jornada = str(row[5]).strip()
        escala = str(row[6]).strip()
        remoto_int = str(row[7]).strip()
        remoto_rev = str(row[8]).strip()
        chefia_nome = str(row[9]).strip() if row[9] else ""
        chefia_mat = str(row[10]).strip() if row[10] else ""

        # 1. Gerenciar Setor
        setor = Setor.query.filter_by(nome=nome_setor).first()
        if not setor:
            setor = Setor(
                nome=nome_setor,
                sigla=sigla,
                chefia_nome=chefia_nome,
                chefia_matricula=chefia_mat
            )
            db.session.add(setor)
            db.session.flush() # Gera o ID sem commitar tudo ainda
            count_setores += 1

        # 2. Gerenciar Funcionário
        funcionario = Funcionario.query.filter_by(siape=siape).first()
        if not funcionario:
            funcionario = Funcionario(
                nome=nome_func,
                siape=siape,
                lotacao=lotacao,
                jornada=jornada,
                escala=escala,
                trabalho_remoto_integral=remoto_int,
                dias_remoto_revezamento=remoto_rev,
                setor_id=setor.id
            )
            db.session.add(funcionario)
            count_funcs += 1
        else:
            # Atualiza dados se já existir? (Opcional, aqui vamos apenas reportar)
            # print(f"Aviso: Funcionário SIAPE {siape} já existe. Ignorando.")
            pass

    db.session.commit()
    print(f"Importação concluída!")
    print(f"Novos Setores: {count_setores}")
    print(f"Novos Funcionários: {count_funcs}")
    
    # Registrar log de auditoria (precisa de um contexto de request para o current_user, 
    # mas como é script CLI, vamos fazer manual se possível ou pular)
    # registrar_log("Importação em Massa", f"Importados {count_funcs} funcionários de {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 src/import_excel.py <caminho_do_arquivo.xlsx>")
    else:
        with app.app_context():
            import_from_excel(sys.argv[1])
