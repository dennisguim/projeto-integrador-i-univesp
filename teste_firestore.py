import firebase_admin
from firebase_admin import credentials, firestore
import os

def testar_conexao():
    print("Iniciando teste de conexão com Firestore...")
    
    # Verifica se o arquivo de credenciais existe
    if not os.path.exists("google-credentials.json"):
        print("ERRO: Arquivo 'google-credentials.json' não encontrado na raiz!")
        return

    try:
        # Inicializa o SDK
        cred = credentials.Certificate("google-credentials.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()

        # Tenta gravar um dado de teste
        print("Tentando gravar um documento de teste...")
        doc_ref = db.collection('teste_sistema').document('status')
        doc_ref.set({
            'mensagem': 'Conexão estabelecida com sucesso!',
            'data': firestore.SERVER_TIMESTAMP,
            'projeto': 'Sistema de Frequência'
        })

        # Tenta ler o dado de volta
        doc = doc_ref.get()
        if doc.exists:
            print(f"SUCESSO! O Google respondeu: {doc.to_dict()['mensagem']}")
            print("Seu banco de dados na nuvem está pronto para uso.")
        else:
            print("ERRO: O documento foi gravado mas não pôde ser lido.")

    except Exception as e:
        print(f"ERRO DE CONEXÃO: {str(e)}")

if __name__ == "__main__":
    testar_conexao()
