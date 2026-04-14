"""
main.py - Ponto de entrada da aplicação FastAPI

Este arquivo:
1. Cria o app FastAPI
2. Cria as tabelas no banco (se não existirem)
3. Registra todos os routers (grupos de endpoints)
4. Configura CORS (permite que o frontend acesse a API)
5. Define os departamentos padrão da igreja no primeiro uso
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import auth, usuarios, departamentos, dias_culto, escalas, notificacoes, cnpj


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executado na inicialização do servidor:
    - Cria todas as tabelas no banco de dados automaticamente
    """
    print("Iniciando Hineni - Sistema de Escalas da Igreja...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas/verificadas no banco de dados.")
    yield
    print("Servidor encerrado.")


# ============================================================
# CRIAÇÃO DO APP FASTAPI
# ============================================================

app = FastAPI(
    title="Hineni - Sistema de Escalas",
    description="""
    Sistema completo para gerenciar escalas de departamentos da Igreja.

    ## Funcionalidades
    * Gerenciamento de membros por departamento
    * Montagem de escalas mensais
    * Verificação automática de conflitos de escala
    * Notificações via App e WhatsApp
    * Geração de PDF calendário
    * Dias de culto recorrentes e esporádicos

    ## Níveis de Acesso
    * **Pastor Presidente**: Acesso total
    * **Líder**: Gerencia os próprios departamentos
    * **Membro**: Visualiza as próprias escalas
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================
# CORS - Permite que o frontend (Flet/web) acesse a API
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8550",   # Frontend Flet em desenvolvimento
        "http://localhost:3000",   # React (se usar futuramente)
        "http://127.0.0.1:8550",
        "*"  # Em produção, substitua pelo domínio real
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTRO DOS ROUTERS
# ============================================================

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(departamentos.router)
app.include_router(dias_culto.router)
app.include_router(escalas.router)
app.include_router(notificacoes.router)
app.include_router(cnpj.router)


# ============================================================
# ENDPOINTS RAIZ
# ============================================================

@app.get("/", tags=["Raiz"])
def raiz():
    """Verifica se a API está funcionando"""
    return {
        "status": "online",
        "sistema": "Hineni - Sistema de Escalas da Igreja",
        "versao": "1.0.0",
        "docs": "/docs"
    }


@app.get("/saude", tags=["Raiz"])
def verificar_saude():
    """Health check - usado para monitoramento"""
    return {"status": "saudável"}
