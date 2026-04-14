"""
routers/dias_culto.py - Gerenciamento dos dias de culto

Rotas:
  GET    /dias-culto       → Lista dias de culto da Igreja
  POST   /dias-culto       → Cria um novo dia de culto
  PUT    /dias-culto/{id}  → Atualiza dia de culto
  DELETE /dias-culto/{id}  → Desativa dia de culto
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import obter_usuario_ativo, exigir_pastor_presidente

router = APIRouter(prefix="/dias-culto", tags=["Dias de Culto"])


@router.get(
    "",
    response_model=List[schemas.DiaCultoResposta],
    summary="Listar dias de culto"
)
def listar_dias_culto(
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    dias = db.query(models.DiaCulto).filter(
        models.DiaCulto.igreja_id == usuario_atual.igreja_id,
        models.DiaCulto.ativo == True
    ).all()
    return dias


@router.post(
    "",
    response_model=schemas.DiaCultoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar dia de culto"
)
def criar_dia_culto(
    dados: schemas.DiaCultoCriar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    """
    O Pastor Presidente configura os dias de culto da Igreja.
    Exemplos:
    - Recorrente: toda Terça às 19:30
    - Esporádico: Retiro Espiritual em 20/07/2025
    """
    novo_dia = models.DiaCulto(
        igreja_id=usuario_atual.igreja_id,
        descricao=dados.descricao,
        recorrente=dados.recorrente,
        dia_semana=dados.dia_semana,
        data_especifica=dados.data_especifica,
        horario=dados.horario,
    )
    db.add(novo_dia)
    db.commit()
    db.refresh(novo_dia)
    return novo_dia


@router.put(
    "/{dia_id}",
    response_model=schemas.DiaCultoResposta,
    summary="Atualizar dia de culto"
)
def atualizar_dia_culto(
    dia_id: int,
    dados: schemas.DiaCultoCriar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    dia = db.query(models.DiaCulto).filter(
        models.DiaCulto.id == dia_id,
        models.DiaCulto.igreja_id == usuario_atual.igreja_id
    ).first()
    if not dia:
        raise HTTPException(status_code=404, detail="Dia de culto não encontrado")

    for campo, valor in dados.model_dump().items():
        setattr(dia, campo, valor)

    db.commit()
    db.refresh(dia)
    return dia


@router.delete(
    "/{dia_id}",
    response_model=schemas.MensagemResposta,
    summary="Desativar dia de culto"
)
def desativar_dia_culto(
    dia_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    dia = db.query(models.DiaCulto).filter(
        models.DiaCulto.id == dia_id,
        models.DiaCulto.igreja_id == usuario_atual.igreja_id
    ).first()
    if not dia:
        raise HTTPException(status_code=404, detail="Dia de culto não encontrado")

    dia.ativo = False
    db.commit()
    return schemas.MensagemResposta(mensagem="Dia de culto desativado com sucesso")
