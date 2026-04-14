"""
dependencies.py - Dependências reutilizáveis do FastAPI

O sistema de Dependency Injection do FastAPI permite que você
"injete" dependências nos seus endpoints automaticamente.

Exemplo de uso em um endpoint:
    @router.get("/meu-perfil")
    def meu_perfil(usuario_atual = Depends(obter_usuario_atual)):
        return usuario_atual

Isso garante que:
1. O token JWT é verificado automaticamente
2. O usuário logado é carregado do banco
3. Se o token for inválido, retorna 401 Unauthorized automaticamente
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import decodificar_token
from app import models

# Define onde o token JWT será procurado nas requisições
# O cliente deve enviar: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Usuario:
    """
    Decodifica o token JWT e retorna o usuário logado.
    Levanta HTTPException 401 se o token for inválido.
    """
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    dados = decodificar_token(token)
    if dados is None:
        raise excecao_credenciais

    usuario_id: int = dados.get("sub")
    if usuario_id is None:
        raise excecao_credenciais

    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == int(usuario_id),
        models.Usuario.ativo == True
    ).first()

    if usuario is None:
        raise excecao_credenciais

    return usuario


def obter_usuario_ativo(
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
) -> models.Usuario:
    """Garante que o usuário está ativo no sistema"""
    if not usuario_atual.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    return usuario_atual


def exigir_pastor_presidente(
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
) -> models.Usuario:
    """Apenas o Pastor Presidente pode acessar"""
    if usuario_atual.role != models.RoleUsuario.PASTOR_PRESIDENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Pastor Presidente"
        )
    return usuario_atual


def exigir_lider_ou_superior(
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
) -> models.Usuario:
    """Líder ou Pastor Presidente podem acessar"""
    roles_permitidas = {
        models.RoleUsuario.PASTOR_PRESIDENTE,
        models.RoleUsuario.LIDER
    }
    if usuario_atual.role not in roles_permitidas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a líderes e pastor presidente"
        )
    return usuario_atual
