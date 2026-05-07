import firebase_admin
from firebase_admin import credentials, firestore
import openpyxl
import os
import sys

# 1. Configuração do Firebase
# Ajuste o caminho se necessário (assume que o .json está na raiz)
CRED_PATH = "google-credentials.json"

if not firebase_admin._apps:
    if not os.path.exists(CRED_PATH):
        print(f"Erro: Arquivo {CRED_PATH} não encontrado!")
        sys.exit(1)
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def importar_excel_para_firestore(file_path):
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return

    print(f"Lendo arquivo: {file_path}")
    try:
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
    except Exception as e:
        print(f"Erro ao abrir Excel: {e}")
        return

    # Espera que o cabeçalho esteja na linha 1
    # Colunas esperadas: 
    # 0: SETOR, 1: SIGLA, 2: LOTAÇÃO, 3: SIAPE, 4: NOME, 
    # 5: JORNADA, 6: ESCALA, 7: REMOTO_INT, 8: REMOTO_REV,
    # 9: CHEFIA_NOME, 10: CHEFIA_MATRICULA

    count_setores = 0
    count_funcs = 0

    print("Iniciando importação para o Firestore...")

    # Cache de setores para evitar múltiplas consultas
    setores_cache = {}
    
    # Busca setores existentes no Firestore
    setores_ref = db.collection('setores').get()
    for s in setores_ref:
        setores_cache[s.to_dict()['nome'].upper()] = s.id

    # Iterar a partir da linha 2
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # Validação básica ajustada para os novos índices (A é vazia, então começamos em B=1)
        if len(row) < 6 or not row[1] or not row[4] or not row[5]:
            continue

        nome_setor = str(row[1]).strip().upper()
        sigla = str(row[2]).strip().upper() if row[2] else ""
        lotacao = str(row[3]).strip().upper() if row[3] else ""
        siape = str(row[4]).strip()
        nome_func = str(row[5]).strip().upper()
        jornada = str(row[6]).strip() if row[6] else ""
        escala = str(row[7]).strip() if row[7] else ""
        remoto_int = str(row[8]).strip() if row[8] else "NÃO"
        remoto_rev = str(row[9]).strip() if row[9] else "NÃO"
        chefia_nome = str(row[10]).strip() if len(row) > 10 and row[10] else ""
        chefia_mat = str(row[11]).strip() if len(row) > 11 and row[11] else ""

        # 1. Gerenciar Setor
        if nome_setor not in setores_cache:
            # Cria novo setor no Firestore
            novo_setor_ref = db.collection('setores').document() # Gera ID automático
            novo_setor_ref.set({
                'nome': nome_setor,
                'sigla': sigla,
                'lotacao': lotacao,
                'chefia_nome': chefia_nome,
                'chefia_matricula': chefia_mat
            })
            setores_cache[nome_setor] = novo_setor_ref.id
            count_setores += 1
            print(f"Novo setor criado: {nome_setor}")

        setor_id = setores_cache[nome_setor]

        # 2. Gerenciar Funcionário
        # Verifica se o funcionário já existe pelo SIAPE
        func_query = db.collection('funcionarios').where('siape', '==', siape).limit(1).get()
        
        if not func_query:
            # Adiciona novo funcionário
            db.collection('funcionarios').add({
                'nome': nome_func,
                'siape': siape,
                'lotacao': lotacao,
                'jornada': jornada,
                'escala': escala,
                'trabalho_remoto_integral': remoto_int,
                'dias_remoto_revezamento': remoto_rev,
                'setor_id': str(setor_id)
            })
            count_funcs += 1
            if count_funcs % 10 == 0:
                print(f"{count_funcs} funcionários importados...")
        else:
            # Opcional: Atualizar dados do funcionário existente
            pass

    print(f"\nImportação concluída com sucesso!")
    print(f"Novos Setores: {count_setores}")
    print(f"Novos Funcionários: {count_funcs}")
    print("-" * 30)

if __name__ == "__main__":
    file_name = "planilha_importacao_modelo.xlsx"
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    
    importar_excel_para_firestore(file_name)
