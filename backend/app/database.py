"""
database.py - Configuração da conexão com o PostgreSQL

SQLAlchemy é uma biblioteca que nos permite trabalhar com bancos de dados
usando Python, sem precisar escrever SQL puro na maioria das vezes.

Conceitos importantes:
- engine: é a "ponte" entre Python e o banco de dados
- SessionLocal: é como uma "sessão de trabalho" com o banco
- Base: é a classe base que todos os nossos modelos (tabelas) vão herdar
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

# URL de conexão com o banco de dados
# Formato: postgresql://usuario:senha@host:porta/nome_do_banco
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hineni:hineni123@localhost:5432/hineni_db"
)

# Cria o motor de conexão com o banco
engine = create_engine(DATABASE_URL)

# Cria a fábrica de sessões
# autocommit=False: mudanças precisam ser confirmadas manualmente (mais seguro)
# autoflush=False: não envia SQL automaticamente antes de cada query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para todos os modelos (tabelas) do banco
Base = declarative_base()


def get_db():
    """
    Função geradora que abre e fecha uma sessão com o banco.
    Usada como dependência nos endpoints da API (FastAPI Dependency Injection).

    O 'yield' funciona como: abre a sessão → entrega para o endpoint → fecha no final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
