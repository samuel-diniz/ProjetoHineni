"""
routers/notificacoes.py - Notificações do usuário logado

Rotas:
  GET  /notificacoes          → Listar notificações do usuário
  PUT  /notificacoes/lidas    → Marcar notificações como lidas
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import obter_usuario_ativo

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


@router.get(
    "",
    response_model=List[schemas.NotificacaoResposta],
    summary="Minhas notificações"
)
def listar_notificacoes(
    apenas_nao_lidas: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """Retorna as notificações do usuário logado, da mais recente para a mais antiga."""
    query = db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == usuario_atual.id
    )
    if apenas_nao_lidas:
        query = query.filter(models.Notificacao.lida == False)

    return query.order_by(models.Notificacao.criado_em.desc()).limit(50).all()


@router.put(
    "/lidas",
    response_model=schemas.MensagemResposta,
    summary="Marcar notificações como lidas"
)
def marcar_como_lidas(
    dados: schemas.MarcarLidaRequest,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """Marca uma lista de notificações como lidas."""
    db.query(models.Notificacao).filter(
        models.Notificacao.id.in_(dados.notificacao_ids),
        models.Notificacao.usuario_id == usuario_atual.id
    ).update({"lida": True}, synchronize_session=False)

    db.commit()
    return schemas.MensagemResposta(mensagem="Notificações marcadas como lidas")
