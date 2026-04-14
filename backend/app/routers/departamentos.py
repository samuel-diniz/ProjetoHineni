"""
routers/departamentos.py - Gerenciamento de departamentos

Rotas:
  GET    /departamentos             → Lista departamentos da Igreja
  POST   /departamentos             → Cria um novo departamento
  PUT    /departamentos/{id}        → Atualiza departamento
  DELETE /departamentos/{id}        → Desativa departamento

  GET    /departamentos/{id}/membros         → Lista membros do departamento
  POST   /departamentos/{id}/membros         → Adiciona membro ao departamento
  DELETE /departamentos/{id}/membros/{uid}   → Remove membro do departamento
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import obter_usuario_ativo, exigir_lider_ou_superior, exigir_pastor_presidente

router = APIRouter(prefix="/departamentos", tags=["Departamentos"])


@router.get(
    "",
    response_model=List[schemas.DepartamentoResposta],
    summary="Listar departamentos da Igreja"
)
def listar_departamentos(
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    departamentos = db.query(models.Departamento).filter(
        models.Departamento.igreja_id == usuario_atual.igreja_id,
        models.Departamento.ativo == True
    ).order_by(models.Departamento.nome).all()

    resultado = []
    for dept in departamentos:
        total = db.query(models.UsuarioDepartamento).filter(
            models.UsuarioDepartamento.departamento_id == dept.id
        ).count()
        resposta = schemas.DepartamentoResposta(
            **{c.name: getattr(dept, c.name) for c in dept.__table__.columns},
            total_membros=total
        )
        resultado.append(resposta)

    return resultado


@router.post(
    "",
    response_model=schemas.DepartamentoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo departamento"
)
def criar_departamento(
    dados: schemas.DepartamentoCriar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    """Apenas o Pastor Presidente pode criar departamentos"""
    # Verifica se já existe um departamento com esse nome na Igreja
    existente = db.query(models.Departamento).filter(
        models.Departamento.igreja_id == usuario_atual.igreja_id,
        models.Departamento.nome == dados.nome
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um departamento com o nome '{dados.nome}'"
        )

    novo_dept = models.Departamento(
        igreja_id=usuario_atual.igreja_id,
        nome=dados.nome,
        descricao=dados.descricao,
        cor=dados.cor or "#3B82F6"
    )
    db.add(novo_dept)
    db.commit()
    db.refresh(novo_dept)

    return schemas.DepartamentoResposta(
        **{c.name: getattr(novo_dept, c.name) for c in novo_dept.__table__.columns},
        total_membros=0
    )


@router.put(
    "/{departamento_id}",
    response_model=schemas.DepartamentoResposta,
    summary="Atualizar departamento"
)
def atualizar_departamento(
    departamento_id: int,
    dados: schemas.DepartamentoAtualizar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_pastor_presidente)
):
    dept = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id,
        models.Departamento.igreja_id == usuario_atual.igreja_id
    ).first()

    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")

    dados_dict = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_dict.items():
        setattr(dept, campo, valor)

    db.commit()
    db.refresh(dept)

    total = db.query(models.UsuarioDepartamento).filter(
        models.UsuarioDepartamento.departamento_id == dept.id
    ).count()

    return schemas.DepartamentoResposta(
        **{c.name: getattr(dept, c.name) for c in dept.__table__.columns},
        total_membros=total
    )


# -------- Membros do Departamento --------

@router.get(
    "/{departamento_id}/membros",
    response_model=List[schemas.UsuarioResposta],
    summary="Listar membros de um departamento"
)
def listar_membros_departamento(
    departamento_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    dept = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id,
        models.Departamento.igreja_id == usuario_atual.igreja_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")

    membros = (
        db.query(models.Usuario)
        .join(models.UsuarioDepartamento)
        .filter(
            models.UsuarioDepartamento.departamento_id == departamento_id,
            models.Usuario.ativo == True
        )
        .order_by(models.Usuario.nome)
        .all()
    )
    return membros


@router.post(
    "/{departamento_id}/membros",
    response_model=schemas.MensagemResposta,
    summary="Adicionar membro ao departamento"
)
def adicionar_membro(
    departamento_id: int,
    dados: schemas.AdicionarMembroDepartamento,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Adiciona um membro ao departamento.
    Um líder só pode adicionar membros ao departamento que ele lidera.
    O Pastor Presidente pode adicionar em qualquer departamento.
    """
    # Verifica se o departamento pertence à Igreja
    dept = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id,
        models.Departamento.igreja_id == usuario_atual.igreja_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")

    # Líderes só podem gerenciar o próprio departamento
    if usuario_atual.role == models.RoleUsuario.LIDER:
        eh_lider = db.query(models.UsuarioDepartamento).filter(
            models.UsuarioDepartamento.usuario_id == usuario_atual.id,
            models.UsuarioDepartamento.departamento_id == departamento_id,
            models.UsuarioDepartamento.is_lider == True
        ).first()
        if not eh_lider:
            raise HTTPException(status_code=403, detail="Você não é líder deste departamento")

    # Verifica se o usuário existe na mesma Igreja
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == dados.usuario_id,
        models.Usuario.igreja_id == usuario_atual.igreja_id
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica se já está no departamento
    ja_existe = db.query(models.UsuarioDepartamento).filter(
        models.UsuarioDepartamento.usuario_id == dados.usuario_id,
        models.UsuarioDepartamento.departamento_id == departamento_id
    ).first()
    if ja_existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{usuario.nome} já está no departamento {dept.nome}"
        )

    nova_entrada = models.UsuarioDepartamento(
        usuario_id=dados.usuario_id,
        departamento_id=departamento_id,
        is_lider=dados.is_lider
    )
    db.add(nova_entrada)
    db.commit()

    return schemas.MensagemResposta(
        mensagem=f"{usuario.nome} adicionado ao departamento {dept.nome} com sucesso"
    )


@router.delete(
    "/{departamento_id}/membros/{usuario_id}",
    response_model=schemas.MensagemResposta,
    summary="Remover membro do departamento"
)
def remover_membro(
    departamento_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    entrada = db.query(models.UsuarioDepartamento).filter(
        models.UsuarioDepartamento.usuario_id == usuario_id,
        models.UsuarioDepartamento.departamento_id == departamento_id
    ).first()

    if not entrada:
        raise HTTPException(status_code=404, detail="Membro não encontrado neste departamento")

    db.delete(entrada)
    db.commit()
    return schemas.MensagemResposta(mensagem="Membro removido do departamento com sucesso")
