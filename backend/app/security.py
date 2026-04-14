"""
security.py - Autenticação e segurança

JWT (JSON Web Token) é como um "crachá digital":
- No login, geramos um token com os dados do usuário
- O usuário envia esse token em cada requisição (como mostrar o crachá)
- Verificamos se o token é válido antes de permitir o acesso

bcrypt é um algoritmo de hash de senhas:
- Nunca salvamos a senha real no banco, só o hash
- hash("123456") → "$2b$12$xyz..." (impossível de reverter)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

# Configurações do JWT
SECRET_KEY              = os.getenv("SECRET_KEY", "chave-padrao-TROQUE-em-producao")
ALGORITHM               = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Contexto de hash de senhas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """
    Converte a senha em hash antes de salvar no banco.
    Exemplo: "minhasenha123" → "$2b$12$abc..."
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """
    Verifica se a senha digitada bate com o hash salvo no banco.
    Retorna True se correto, False se errado.
    """
    return pwd_context.verify(senha_plana, senha_hash)


def criar_token_acesso(dados: dict, expira_em: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados do usuário.

    O token contém:
    - sub: ID do usuário
    - exp: quando o token expira
    - (outros dados que você queira incluir)
    """
    dados_para_codificar = dados.copy()

    if expira_em:
        expiracao = datetime.now(timezone.utc) + expira_em
    else:
        expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)

    dados_para_codificar.update({"exp": expiracao})

    # jwt.encode() "assina" os dados com a SECRET_KEY
    token = jwt.encode(dados_para_codificar, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decodificar_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida o token JWT.
    Retorna os dados do token se válido, None se inválido/expirado.
    """
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return dados
    except JWTError:
        return None
