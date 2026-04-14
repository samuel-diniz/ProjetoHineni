"""
services/pdf_service.py - Geração de PDF em formato calendário

Gera um PDF com o calendário do mês mostrando:
- Cada dia da semana como coluna
- Dias numerados
- Nome da pessoa escalada em cada dia
- Cores por departamento
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import calendar
import io
from datetime import date
from app import models

# Dias da semana em português
DIAS_SEMANA_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def gerar_pdf_escala(escala: models.Escala) -> bytes:
    """
    Gera um PDF em formato de calendário para a escala dada.

    Retorna os bytes do PDF, que podem ser enviados como resposta HTTP
    ou salvos em arquivo.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1 * cm
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Heading1"],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    estilo_subtitulo = ParagraphStyle(
        "SubTitulo",
        parent=estilos["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    estilo_celula = ParagraphStyle(
        "Celula",
        parent=estilos["Normal"],
        fontSize=8,
        alignment=TA_CENTER,
    )

    # Cor do departamento (ex: "#3B82F6")
    cor_dept_hex = escala.departamento.cor.lstrip("#")
    r = int(cor_dept_hex[0:2], 16) / 255
    g = int(cor_dept_hex[2:4], 16) / 255
    b = int(cor_dept_hex[4:6], 16) / 255
    cor_dept = colors.Color(r, g, b)

    nome_mes = NOMES_MESES[escala.mes]
    nome_igreja = escala.departamento.igreja.nome if escala.departamento.igreja else "Igreja"

    # Agrupa entradas por data
    entradas_por_data: dict[date, list[str]] = {}
    for entrada in escala.entradas:
        if entrada.data not in entradas_por_data:
            entradas_por_data[entrada.data] = []
        nome_curto = entrada.usuario.nome.split()[0]  # Primeiro nome
        cargo = entrada.usuario.cargo.value
        entradas_por_data[entrada.data].append(f"{cargo}\n{nome_curto}")

    # Monta o calendário
    cal = calendar.monthcalendar(escala.ano, escala.mes)

    # Cabeçalho da tabela
    cabecalho = [Paragraph(f"<b>{d}</b>", estilo_celula) for d in DIAS_SEMANA_PT]
    linhas_tabela = [cabecalho]

    for semana in cal:
        linha = []
        for dia in semana:
            if dia == 0:
                linha.append("")  # Célula vazia
            else:
                data_atual = date(escala.ano, escala.mes, dia)
                nomes = entradas_por_data.get(data_atual, [])
                conteudo = f"<b>{dia}</b>"
                if nomes:
                    conteudo += "\n" + "\n".join(nomes)
                linha.append(Paragraph(conteudo, estilo_celula))
        linhas_tabela.append(linha)

    # Define as larguras das colunas (7 dias, dividindo a largura da página)
    largura_pagina = landscape(A4)[0] - 2 * cm  # Margem
    largura_col = largura_pagina / 7
    larguras_colunas = [largura_col] * 7

    # Cria a tabela
    tabela = Table(linhas_tabela, colWidths=larguras_colunas, rowHeights=[1.2 * cm] + [3.5 * cm] * len(cal))

    tabela.setStyle(TableStyle([
        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), cor_dept),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 11),

        # Corpo
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.Color(0.97, 0.97, 0.97), colors.white]),

        # Grade
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOX",  (0, 0), (-1, -1), 1,   colors.black),

        # Alinhamento
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),

        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),

        # Destaque Domingo (coluna 6)
        ("BACKGROUND", (6, 1), (6, -1), colors.Color(1, 0.95, 0.9)),
    ]))

    # Monta o documento
    conteudo = [
        Paragraph(nome_igreja, estilo_titulo),
        Paragraph(
            f"Escala de {escala.departamento.nome} — {nome_mes}/{escala.ano}",
            estilo_subtitulo
        ),
        tabela,
        Spacer(1, 0.3 * cm),
        Paragraph(
            f"Gerado em {date.today().strftime('%d/%m/%Y')} · Hineni - Sistema de Escalas",
            ParagraphStyle("Rodape", parent=estilos["Normal"], fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
        )
    ]

    doc.build(conteudo)
    buffer.seek(0)
    return buffer.read()
