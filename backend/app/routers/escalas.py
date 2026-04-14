"""
routers/escalas.py - Gerenciamento de escalas

Rotas:
  GET    /escalas                              → Lista escalas do usuário/departamento
  POST   /escalas                              → Cria nova escala (rascunho)
  GET    /escalas/{id}                         → Detalhes da escala com todas as entradas
  DELETE /escalas/{id}                         → Apaga escala em rascunho

  POST   /escalas/{id}/entradas                → Adiciona pessoa à escala (com verificação de conflito)
  DELETE /escalas/{id}/entradas/{entrada_id}   → Remove pessoa da escala

  POST   /escalas/{id}/publicar                → Publica escala e notifica membros
  GET    /escalas/{id}/pdf                     → Gera PDF calendário da escala

  GET    /escalas/verificar-conflito           → Verifica se há conflito antes de escalar
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models, schemas
from app.dependencies import obter_usuario_ativo, exigir_lider_ou_superior
from app.services.notification_service import notificar_publicacao_escala

router = APIRouter(prefix="/escalas", tags=["Escalas"])


def _verificar_conflito(usuario_id: int, data_culto: date, escala_id_ignorar: int, db: Session):
    """
    Verifica se um usuário já está escalado em OUTRO departamento na mesma data.
    Retorna a entrada conflitante ou None.
    """
    conflito = (
        db.query(models.EntradaEscala)
        .join(models.Escala)
        .filter(
            models.EntradaEscala.usuario_id == usuario_id,
            models.EntradaEscala.data == data_culto,
            models.EntradaEscala.escala_id != escala_id_ignorar
        )
        .first()
    )
    return conflito


@router.get(
    "",
    response_model=List[schemas.EscalaResposta],
    summary="Listar escalas"
)
def listar_escalas(
    departamento_id: Optional[int] = None,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """
    Lista as escalas disponíveis.
    - Membros veem apenas escalas PUBLICADAS dos seus departamentos
    - Líderes veem escalas (rascunho + publicadas) dos seus departamentos
    - Pastor Presidente vê todas
    """
    query = (
        db.query(models.Escala)
        .join(models.Departamento)
        .filter(models.Departamento.igreja_id == usuario_atual.igreja_id)
    )

    if departamento_id:
        query = query.filter(models.Escala.departamento_id == departamento_id)
    if mes:
        query = query.filter(models.Escala.mes == mes)
    if ano:
        query = query.filter(models.Escala.ano == ano)

    # Membros só veem escalas publicadas dos seus departamentos
    if usuario_atual.role == models.RoleUsuario.MEMBRO:
        dept_ids = [
            ud.departamento_id for ud in usuario_atual.departamentos
        ]
        query = query.filter(
            models.Escala.departamento_id.in_(dept_ids),
            models.Escala.status == models.StatusEscala.PUBLICADA
        )
    # Líderes veem apenas os seus departamentos
    elif usuario_atual.role == models.RoleUsuario.LIDER:
        dept_ids_lider = [
            ud.departamento_id for ud in usuario_atual.departamentos
            if ud.is_lider
        ]
        query = query.filter(models.Escala.departamento_id.in_(dept_ids_lider))

    escalas = query.order_by(models.Escala.ano.desc(), models.Escala.mes.desc()).all()

    resultado = []
    for escala in escalas:
        total = db.query(models.EntradaEscala).filter(
            models.EntradaEscala.escala_id == escala.id
        ).count()
        resp = schemas.EscalaResposta(
            **{c.name: getattr(escala, c.name) for c in escala.__table__.columns},
            total_entradas=total
        )
        resultado.append(resp)

    return resultado


@router.post(
    "",
    response_model=schemas.EscalaResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova escala (rascunho)"
)
def criar_escala(
    dados: schemas.EscalaCriar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Cria uma nova escala em status RASCUNHO.
    O líder monta a escala e só publica quando estiver pronta.
    """
    # Líderes só podem criar escala no próprio departamento
    if usuario_atual.role == models.RoleUsuario.LIDER:
        eh_lider = db.query(models.UsuarioDepartamento).filter(
            models.UsuarioDepartamento.usuario_id == usuario_atual.id,
            models.UsuarioDepartamento.departamento_id == dados.departamento_id,
            models.UsuarioDepartamento.is_lider == True
        ).first()
        if not eh_lider:
            raise HTTPException(status_code=403, detail="Você não é líder deste departamento")

    # Verifica se já existe escala para este mês/departamento
    existente = db.query(models.Escala).filter(
        models.Escala.departamento_id == dados.departamento_id,
        models.Escala.mes == dados.mes,
        models.Escala.ano == dados.ano
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma escala para este departamento em {dados.mes}/{dados.ano}"
        )

    nova_escala = models.Escala(
        departamento_id=dados.departamento_id,
        mes=dados.mes,
        ano=dados.ano,
        prazo_limite=dados.prazo_limite,
        criado_por_id=usuario_atual.id
    )
    db.add(nova_escala)
    db.commit()
    db.refresh(nova_escala)

    return schemas.EscalaResposta(
        **{c.name: getattr(nova_escala, c.name) for c in nova_escala.__table__.columns},
        total_entradas=0
    )


@router.get(
    "/{escala_id}",
    response_model=List[schemas.EntradaEscalaResposta],
    summary="Ver entradas da escala"
)
def ver_escala(
    escala_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """Retorna todas as entradas (pessoas escaladas) de uma escala"""
    escala = db.query(models.Escala).filter(models.Escala.id == escala_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Escala não encontrada")

    return escala.entradas


@router.post(
    "/{escala_id}/entradas",
    response_model=schemas.EntradaEscalaResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar pessoa à escala"
)
def adicionar_entrada(
    escala_id: int,
    dados: schemas.EntradaEscalaCriar,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Adiciona uma pessoa à escala.

    REGRA PRINCIPAL: Se a pessoa já estiver escalada em outro departamento
    na mesma data, o sistema impede e informa o conflito.
    """
    escala = db.query(models.Escala).filter(models.Escala.id == escala_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Escala não encontrada")

    if escala.status == models.StatusEscala.PUBLICADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Escala já publicada. Crie uma nova versão para editar."
        )

    # Busca o usuário que será escalado
    usuario_escalado = db.query(models.Usuario).filter(
        models.Usuario.id == dados.usuario_id
    ).first()
    if not usuario_escalado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # ===== VERIFICAÇÃO DE CONFLITO =====
    conflito = _verificar_conflito(dados.usuario_id, dados.data, escala_id, db)
    if conflito:
        dept_conflito = conflito.escala.departamento.nome
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{conflito.usuario.cargo.value} {conflito.usuario.nome} já está escalado(a) "
                f"para outro departamento nesta data: {dept_conflito}"
            )
        )

    # Verifica se a pessoa já está nesta mesma escala na mesma data
    ja_escalado = db.query(models.EntradaEscala).filter(
        models.EntradaEscala.escala_id == escala_id,
        models.EntradaEscala.usuario_id == dados.usuario_id,
        models.EntradaEscala.data == dados.data
    ).first()
    if ja_escalado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{usuario_escalado.nome} já está nesta escala nesta data"
        )

    nova_entrada = models.EntradaEscala(
        escala_id=escala_id,
        usuario_id=dados.usuario_id,
        dia_culto_id=dados.dia_culto_id,
        data=dados.data,
        observacao=dados.observacao
    )
    db.add(nova_entrada)
    db.commit()
    db.refresh(nova_entrada)
    return nova_entrada


@router.delete(
    "/{escala_id}/entradas/{entrada_id}",
    response_model=schemas.MensagemResposta,
    summary="Remover pessoa da escala"
)
def remover_entrada(
    escala_id: int,
    entrada_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    entrada = db.query(models.EntradaEscala).filter(
        models.EntradaEscala.id == entrada_id,
        models.EntradaEscala.escala_id == escala_id
    ).first()
    if not entrada:
        raise HTTPException(status_code=404, detail="Entrada não encontrada")

    db.delete(entrada)
    db.commit()
    return schemas.MensagemResposta(mensagem="Pessoa removida da escala com sucesso")


@router.post(
    "/{escala_id}/publicar",
    response_model=schemas.MensagemResposta,
    summary="Publicar escala e notificar membros"
)
def publicar_escala(
    escala_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Publica a escala:
    1. Muda o status para PUBLICADA
    2. Envia notificações (App + WhatsApp) para todos os escalados
    """
    from datetime import datetime

    escala = db.query(models.Escala).filter(models.Escala.id == escala_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Escala não encontrada")

    if escala.status == models.StatusEscala.PUBLICADA:
        raise HTTPException(status_code=400, detail="Escala já está publicada")

    if not escala.entradas:
        raise HTTPException(status_code=400, detail="Não é possível publicar uma escala vazia")

    escala.status = models.StatusEscala.PUBLICADA
    escala.publicada_em = datetime.utcnow()
    db.commit()

    # Envia notificações em background (não bloqueia a resposta)
    background_tasks.add_task(notificar_publicacao_escala, escala_id, db)

    nome_mes = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ][escala.mes]

    return schemas.MensagemResposta(
        mensagem=(
            f"Escala de {escala.departamento.nome} - {nome_mes}/{escala.ano} "
            f"publicada! Notificações enviadas."
        )
    )


@router.get(
    "/{escala_id}/pdf",
    summary="Gerar PDF calendário da escala"
)
def gerar_pdf(
    escala_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_ativo)
):
    """Gera e retorna um PDF com o calendário da escala"""
    from app.services.pdf_service import gerar_pdf_escala

    escala = db.query(models.Escala).filter(models.Escala.id == escala_id).first()
    if not escala:
        raise HTTPException(status_code=404, detail="Escala não encontrada")

    pdf_bytes = gerar_pdf_escala(escala)
    nome_mes = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"][escala.mes]
    filename = f"escala_{escala.departamento.nome}_{nome_mes}{escala.ano}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get(
    "/{escala_id}/verificar-conflito",
    summary="Verificar conflito antes de escalar"
)
def verificar_conflito(
    escala_id: int,
    usuario_id: int,
    data: date,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(exigir_lider_ou_superior)
):
    """
    Verifica previamente se há conflito, antes de tentar adicionar.
    Útil para mostrar um aviso no frontend antes de salvar.
    """
    conflito = _verificar_conflito(usuario_id, data, escala_id, db)
    if conflito:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        return {
            "tem_conflito": True,
            "mensagem": (
                f"{conflito.usuario.cargo.value} {conflito.usuario.nome} já está escalado(a) "
                f"em: {conflito.escala.departamento.nome} no dia {data.strftime('%d/%m/%Y')}"
            )
        }
    return {"tem_conflito": False, "mensagem": "Sem conflitos"}
