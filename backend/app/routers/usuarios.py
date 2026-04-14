"""
routers/usuarios.py - Gerenciamento de usuários

Rotas:
  GET    /usuarios             → Lista todos os usuários da Igreja
  GET    /usuarios/{id}        → Detalhes de um usuário
  PUT    /usuarios/{id}        → Atualiza dados de um usuário
  DELETE /usuarios/{id}        → Desativa um usuário (soft delete)
  PUT    /usuarios/{id}/role   → Altera o role (apenas Pastor Presidente)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas
from app.dependencies import (
    obter_usuario_atual,
    obter_usuario_ativo,
    exigir_pastor_presidente,
    exigir_lider_ou_superior,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get(
    "",
    response_model=List[schemas.UsuarioResposta],
    summary="Listar usuários da Igreja"
)
def listar_usuarios(
    role: Optional[models.RoleUsuario] = Query(None, description="Filtrar por role"),
    ativo: bool = Query(True, description="Mostrar apenas ativos"),
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """
    Lista todos os usuários da mesma Igreja do usuário logado.
    Filtros opcionais: role e status ativo.
    """
    query = db.query(models.Usuario).filter(
        models.Usuario.igreja_id == usuario_atual.igreja_id,
        models.Usuario.ativo == ativo
    )
    if role:
        query = query.filter(models.Usuario.role == role)

    return query.order_by(models.Usuario.nome).all()


@router.get(
    "/{usuario_id}",
    response_model=schemas.UsuarioRespostaCompleta,
    summary="Detalhes de um usuário"
)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """Retorna os dados completos de um usuário, incluindo seus departamentos."""
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id,
        models.Usuario.igreja_id == usuario_atual.igreja_id
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Monta a lista de departamentos do usuário
    departamentos = []
    for ud in usuario.departamentos:
        dept_simples = schemas.DepartamentoSimples(
            id=ud.departamento.id,
            nome=ud.departamento.nome,
            cor=ud.departamento.cor,
            is_lider=ud.is_lider
        )
        departamentos.append(dept_simples)

    resposta = schemas.UsuarioRespostaCompleta(
        **schemas.UsuarioResposta.model_validate(usuario).model_dump(),
        departamentos=departamentos
    )
    return resposta


@router.put(
    "/{usuario_id}",
    response_model=schemas.UsuarioResposta,
    summary="Atualizar dados de usuário"
)
def atualizar_usuario(
    usuario_id: int,
    dados: schemas.UsuarioAtualizar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """
    Atualiza dados de um usuário.
    Um usuário pode editar o próprio perfil.
    Líderes e o Pastor podem editar qualquer usuário da Igreja.
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id,
        models.Usuario.igreja_id == usuario_atual.igreja_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Membros só podem editar o próprio perfil
    if usuario_atual.role == models.RoleUsuario.MEMBRO and usuario_atual.id != usuario_id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este usuário")

    # Aplica as atualizações apenas nos campos enviados
    dados_dict = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_dict.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete(
    "/{usuario_id}",
    response_model=schemas.MensagemResposta,
    summary="Desativar usuário"
)
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Desativa um usuário (soft delete - não apaga do banco, só marca como inativo).
    Apenas líderes e o Pastor Presidente podem fazer isso.
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id,
        models.Usuario.igreja_id == usuario_atual.igreja_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.id == usuario_atual.id:
        raise HTTPException(status_code=400, detail="Você não pode desativar a si mesmo")

    usuario.ativo = False
    db.commit()
    return schemas.MensagemResposta(mensagem=f"Usuário {usuario.nome} desativado com sucesso")


@router.put(
    "/{usuario_id}/role",
    response_model=schemas.UsuarioResposta,
    summary="Alterar role/permissão de usuário"
)
def alterar_role(
    usuario_id: int,
    novo_role: models.RoleUsuario,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    """
    Altera o nível de acesso de um usuário.
    APENAS o Pastor Presidente pode fazer isso.
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id,
        models.Usuario.igreja_id == usuario_atual.igreja_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.role = novo_role
    db.commit()
    db.refresh(usuario)
    return usuario
