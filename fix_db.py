import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'database.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE setor ADD COLUMN Lotacao TEXT")
    conn.commit()
    print("Coluna 'lotacao' adicionada com sucesso!")
except sqlite3.OperationalError:
    print("A coluna 'lotacao' já existe ou houve erro.")
finally:
    conn.close()