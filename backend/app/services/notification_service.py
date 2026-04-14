"""
services/notification_service.py - Serviço de notificações

Responsável por:
1. Criar registros de notificação no banco (para o App)
2. Enviar mensagens WhatsApp via Evolution API

Quando a escala é publicada, esse serviço envia mensagens para
todos os membros escalados, informando os dias em que vão servir.
"""

import os
import httpx
from sqlalchemy.orm import Session
from datetime import datetime
from app import models

# Configurações da Evolution API (WhatsApp)
WHATSAPP_API_URL  = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
WHATSAPP_API_KEY  = os.getenv("WHATSAPP_API_KEY", "")
WHATSAPP_INSTANCE = os.getenv("WHATSAPP_INSTANCE", "hineni")

# Nomes dos meses em português
NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def criar_notificacao_app(
    db: Session,
    usuario_id: int,
    titulo: str,
    mensagem: str
) -> models.Notificacao:
    """Cria uma notificação no banco (aparece no app do usuário)"""
    notif = models.Notificacao(
        usuario_id=usuario_id,
        titulo=titulo,
        mensagem=mensagem,
        canal=models.CanalNotificacao.APP,
        enviada=True,
        enviada_em=datetime.utcnow()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


async def enviar_whatsapp(telefone: str, mensagem: str) -> bool:
    """
    Envia mensagem WhatsApp usando a Evolution API.

    A Evolution API é gratuita e open-source.
    Documentação: https://doc.evolution-api.com

    Retorna True se enviou com sucesso, False caso contrário.
    """
    if not WHATSAPP_API_KEY or not telefone:
        print(f"[WhatsApp] Pulado (sem configuração ou telefone): {telefone}")
        return False

    # Remove formatação do telefone: apenas números + código do país
    numero_limpo = "".join(filter(str.isdigit, telefone))
    if not numero_limpo.startswith("55"):
        numero_limpo = "55" + numero_limpo  # Adiciona código do Brasil

    url = f"{WHATSAPP_API_URL}/message/sendText/{WHATSAPP_INSTANCE}"
    headers = {"apikey": WHATSAPP_API_KEY, "Content-Type": "application/json"}
    payload = {
        "number": numero_limpo,
        "text": mensagem
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                print(f"[WhatsApp] Mensagem enviada para {numero_limpo}")
                return True
            else:
                print(f"[WhatsApp] Erro {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print(f"[WhatsApp] Falha ao enviar mensagem: {e}")
        return False


def _montar_mensagem_escala(usuario: models.Usuario, escala: models.Escala, datas: list) -> str:
    """
    Monta a mensagem de notificação da escala para um usuário.

    Exemplo de mensagem:
    Olá Pastor João!
    A escala de Obreiros - Maio/2025 foi liberada!
    Você está escalado(a) nos seguintes dias:
    * Domingo, 04/05 às 09h
    * Terça-feira, 06/05 às 19h30
    Chegue de 20 a 30 minutos antes do culto iniciar.
    Consulte o aplicativo Hineni para mais detalhes.
    """
    nome_mes = NOMES_MESES[escala.mes]
    dept_nome = escala.departamento.nome

    # Saudação com cargo
    saudacao = f"{usuario.cargo.value} {usuario.nome.split()[0]}"

    # Lista de dias escalados
    dias_formatados = []
    for entrada in datas:
        dia_semana_pt = {
            "Monday": "Segunda-feira",
            "Tuesday": "Terça-feira",
            "Wednesday": "Quarta-feira",
            "Thursday": "Quinta-feira",
            "Friday": "Sexta-feira",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }.get(entrada.data.strftime("%A"), entrada.data.strftime("%A"))

        horario = entrada.dia_culto.horario.strftime("%Hh%M").replace("h00", "h")
        dias_formatados.append(
            f"  • {dia_semana_pt}, {entrada.data.strftime('%d/%m')} às {horario}"
        )

    dias_str = "\n".join(dias_formatados)

    mensagem = (
        f"Olá {saudacao}! 🙏\n\n"
        f"A escala de *{dept_nome} - {nome_mes}/{escala.ano}* foi liberada!\n\n"
        f"Você está escalado(a) nos seguintes dias:\n"
        f"{dias_str}\n\n"
        f"_Chegue de 20 a 30 minutos antes do culto iniciar._\n\n"
        f"Consulte o aplicativo *Hineni* para mais detalhes. 📅"
    )
    return mensagem


def notificar_publicacao_escala(escala_id: int, db: Session):
    """
    Função chamada em background quando uma escala é publicada.

    Para cada membro escalado:
    1. Cria uma notificação no app
    2. Envia mensagem WhatsApp (se configurado)
    """
    import asyncio

    escala = db.query(models.Escala).filter(models.Escala.id == escala_id).first()
    if not escala:
        print(f"[Notificação] Escala {escala_id} não encontrada")
        return

    # Agrupa entradas por usuário
    entradas_por_usuario: dict[int, list] = {}
    for entrada in escala.entradas:
        uid = entrada.usuario_id
        if uid not in entradas_por_usuario:
            entradas_por_usuario[uid] = []
        entradas_por_usuario[uid].append(entrada)

    nome_mes = NOMES_MESES[escala.mes]
    dept_nome = escala.departamento.nome

    for usuario_id, entradas in entradas_por_usuario.items():
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario:
            continue

        mensagem = _montar_mensagem_escala(usuario, escala, entradas)
        titulo   = f"Escala de {dept_nome} - {nome_mes}/{escala.ano} publicada!"

        # 1. Notificação no app
        criar_notificacao_app(db, usuario_id, titulo, mensagem)

        # 2. WhatsApp (assíncrono)
        if usuario.telefone:
            try:
                asyncio.run(enviar_whatsapp(usuario.telefone, mensagem))
            except Exception as e:
                print(f"[WhatsApp] Erro ao enviar para {usuario.nome}: {e}")

    print(f"[Notificação] Escala {escala_id} - notificações enviadas para {len(entradas_por_usuario)} membros")
