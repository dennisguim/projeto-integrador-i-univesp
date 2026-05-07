import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from src.app import app, db, Usuario, Setor, Funcionario, Frequencia, Log

# 1. Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("google-credentials.json")
    firebase_admin.initialize_app(cred)

db_fs = firestore.client()

def migrar():
    with app.app_context():
        print("--- Iniciando Migração SQLite -> Firestore ---")

        # 1. Migrar Setores
        setores = Setor.query.all()
        print(f"Migrando {len(setores)} setores...")
        for s in setores:
            db_fs.collection('setores').document(str(s.id)).set({
                'nome': s.nome,
                'sigla': s.sigla,
                'lotacao': s.lotacao,
                'chefia_nome': s.chefia_nome,
                'chefia_matricula': s.chefia_matricula
            })

        # 2. Migrar Usuários
        usuarios = Usuario.query.all()
        print(f"Migrando {len(usuarios)} usuários...")
        for u in usuarios:
            db_fs.collection('usuarios').document(str(u.id)).set({
                'nome_usuario': u.nome_usuario,
                'senha': u.senha,
                'perfil': u.perfil,
                'setor_id': str(u.setor_id) if u.setor_id else None
            })

        # 3. Migrar Funcionários
        funcionarios = Funcionario.query.all()
        print(f"Migrando {len(funcionarios)} funcionários...")
        for f in funcionarios:
            db_fs.collection('funcionarios').document(str(f.id)).set({
                'nome': f.nome,
                'siape': f.siape,
                'lotacao': f.lotacao,
                'jornada': f.jornada,
                'escala': f.escala,
                'trabalho_remoto_integral': f.trabalho_remoto_integral,
                'dias_remoto_revezamento': f.dias_remoto_revezamento,
                'setor_id': str(f.setor_id)
            })

        # 4. Migrar Frequências
        frequencias = Frequencia.query.all()
        print(f"Migrando {len(frequencias)} frequências...")
        for freq in frequencias:
            db_fs.collection('frequencias').document(str(freq.id)).set({
                'mes': freq.mes,
                'ano': freq.ano,
                'frequencia_integral': freq.frequencia_integral,
                'observacoes': freq.observacoes,
                'funcionario_id': str(freq.funcionario_id)
            })

        print("\n--- Migração Concluída com Sucesso! ---")
        print("Confira os dados no console do Firebase: Build > Firestore Database")

if __name__ == "__main__":
    migrar()
