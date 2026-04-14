"""
pages/escalas.py - Telas de escalas

Telas:
1. Lista de escalas (filtro por departamento/mês)
2. Detalhes de uma escala (calendário visual)
3. Montagem de escala (adicionar pessoas)
"""

import flet as ft
from datetime import date
from api_client import api

COR_PRIMARIA   = "#1A237E"
COR_SECUNDARIA = "#283593"
COR_DESTAQUE   = "#FFD700"

NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def tela_lista_escalas(page: ft.Page):
    """Tela com a lista de todas as escalas visíveis ao usuário"""
    usuario = api.usuario_atual
    if not usuario:
        page.go("/login")
        return

    role = usuario.get("role", "MEMBRO")
    hoje = date.today()

    # Estado dos filtros
    filtro_mes = ft.Dropdown(
        label="Mês",
        value=str(hoje.month),
        options=[ft.dropdown.Option(str(i), NOMES_MESES[i]) for i in range(1, 13)],
        width=140,
        on_change=lambda e: page.run_task(carregar_escalas)
    )
    filtro_ano = ft.Dropdown(
        label="Ano",
        value=str(hoje.year),
        options=[ft.dropdown.Option(str(a)) for a in range(2024, 2028)],
        width=100,
        on_change=lambda e: page.run_task(carregar_escalas)
    )

    lista_escalas = ft.Column(spacing=10)
    texto_status  = ft.Text("Carregando...", color=ft.Colors.GREY_500, italic=True)

    def cartao_escala(escala: dict) -> ft.Container:
        status = escala.get("status", "")
        cor_status = {
            "PUBLICADA": ft.Colors.GREEN,
            "RASCUNHO":  ft.Colors.ORANGE,
            "ARQUIVADA": ft.Colors.GREY,
        }.get(status, ft.Colors.GREY)

        nome_mes = NOMES_MESES[escala["mes"]]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(
                            f"{nome_mes}/{escala['ano']}",
                            size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA
                        ),
                        ft.Text(
                            f"{escala['total_entradas']} pessoas escaladas",
                            size=12, color=ft.Colors.GREY_600
                        ),
                    ], expand=True),
                    ft.Container(
                        content=ft.Text(status, size=11, color=cor_status, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.with_opacity(0.1, cor_status),
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    )
                ]),
                ft.Divider(height=10),
                ft.Row([
                    ft.TextButton(
                        "Ver detalhes",
                        icon=ft.Icons.VISIBILITY,
                        on_click=lambda e, eid=escala["id"]: page.go(f"/escalas/{eid}")
                    ),
                    ft.TextButton(
                        "Baixar PDF",
                        icon=ft.Icons.PICTURE_AS_PDF,
                        style=ft.ButtonStyle(color=ft.Colors.RED_700),
                        on_click=lambda e, eid=escala["id"]: page.launch_url(
                            f"http://localhost:8000/escalas/{eid}/pdf"
                        ),
                        visible=status == "PUBLICADA"
                    ),
                    # Botão "Montar" só para líderes/pastor
                    ft.TextButton(
                        "Montar Escala",
                        icon=ft.Icons.EDIT_CALENDAR,
                        style=ft.ButtonStyle(color=COR_PRIMARIA),
                        on_click=lambda e, eid=escala["id"]: page.go(f"/escalas/{eid}/montar"),
                        visible=(role in ("LIDER", "PASTOR_PRESIDENTE") and status == "RASCUNHO")
                    ),
                ], spacing=0),
            ], spacing=4),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=ft.padding.all(16),
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_200, offset=ft.Offset(0, 2))
        )

    async def carregar_escalas():
        lista_escalas.controls.clear()
        lista_escalas.controls.append(
            ft.Text("Carregando...", color=ft.Colors.GREY_500, italic=True)
        )
        page.update()

        try:
            mes = int(filtro_mes.value)
            ano = int(filtro_ano.value)
            escalas = await api.listar_escalas(mes=mes, ano=ano)

            lista_escalas.controls.clear()
            if escalas:
                for escala in escalas:
                    lista_escalas.controls.append(cartao_escala(escala))
            else:
                lista_escalas.controls.append(
                    ft.Text("Nenhuma escala encontrada para este período", color=ft.Colors.GREY_500, italic=True, size=14)
                )
        except Exception as err:
            lista_escalas.controls = [ft.Text(f"Erro ao carregar: {err}", color=ft.Colors.RED_400)]

        page.update()

    page.run_task(carregar_escalas)

    acoes_appbar = []
    if role in ("LIDER", "PASTOR_PRESIDENTE"):
        acoes_appbar.append(
            ft.IconButton(
                ft.Icons.ADD,
                icon_color=ft.Colors.WHITE,
                tooltip="Nova Escala",
                on_click=lambda e: page.go("/nova-escala")
            )
        )

    return ft.View(
        "/escalas",
        controls=[
            ft.AppBar(
                title=ft.Text("Escalas", color=ft.Colors.WHITE),
                bgcolor=COR_PRIMARIA,
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                    on_click=lambda e: page.go("/dashboard")
                ),
                actions=acoes_appbar
            ),
            ft.Container(
                content=ft.Column([
                    # Filtros
                    ft.Container(
                        content=ft.Row([filtro_mes, filtro_ano], spacing=12),
                        padding=ft.padding.all(16),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
                    ),
                    # Lista
                    ft.Container(
                        content=lista_escalas,
                        padding=ft.padding.all(16),
                        expand=True,
                    )
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
                expand=True,
            )
        ],
        bgcolor=ft.Colors.GREY_50,
        padding=0,
    )


def tela_nova_escala(page: ft.Page):
    """Formulário para criar uma nova escala"""
    usuario = api.usuario_atual
    if not usuario:
        page.go("/login")
        return

    hoje = date.today()

    dropdown_dept = ft.Dropdown(label="Departamento *", options=[], expand=True)
    dropdown_mes  = ft.Dropdown(
        label="Mês *",
        value=str(hoje.month),
        options=[ft.dropdown.Option(str(i), NOMES_MESES[i]) for i in range(1, 13)],
        expand=True
    )
    dropdown_ano = ft.Dropdown(
        label="Ano *",
        value=str(hoje.year),
        options=[ft.dropdown.Option(str(a)) for a in range(2024, 2028)],
        expand=True
    )
    campo_prazo = ft.TextField(
        label="Prazo limite (AAAA-MM-DD, opcional)",
        hint_text="Ex: 2025-04-25",
        prefix_icon=ft.Icons.CALENDAR_TODAY
    )
    texto_erro = ft.Text("", color=ft.Colors.RED_600, size=13)

    async def carregar_departamentos():
        try:
            depts = await api.listar_departamentos()
            dropdown_dept.options = [
                ft.dropdown.Option(str(d["id"]), d["nome"]) for d in depts
            ]
            if depts:
                dropdown_dept.value = str(depts[0]["id"])
            page.update()
        except Exception as err:
            texto_erro.value = f"Erro ao carregar departamentos: {err}"
            page.update()

    async def criar_escala(e):
        texto_erro.value = ""
        if not dropdown_dept.value:
            texto_erro.value = "Selecione um departamento"
            page.update()
            return

        try:
            prazo = campo_prazo.value.strip() or None
            await api.criar_escala(
                departamento_id=int(dropdown_dept.value),
                mes=int(dropdown_mes.value),
                ano=int(dropdown_ano.value),
                prazo_limite=prazo
            )
            page.go("/escalas")
        except Exception as err:
            texto_erro.value = str(err)
            page.update()

    page.run_task(carregar_departamentos)

    return ft.View(
        "/nova-escala",
        controls=[
            ft.AppBar(
                title=ft.Text("Nova Escala", color=ft.Colors.WHITE),
                bgcolor=COR_PRIMARIA,
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                    on_click=lambda e: page.go("/escalas")
                )
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Criar Nova Escala", size=20, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    ft.Container(height=16),
                    dropdown_dept,
                    ft.Row([dropdown_mes, dropdown_ano], spacing=12),
                    campo_prazo,
                    ft.Container(height=8),
                    texto_erro,
                    ft.Container(height=8),
                    ft.ElevatedButton(
                        "CRIAR ESCALA",
                        icon=ft.Icons.ADD,
                        bgcolor=COR_PRIMARIA,
                        color=ft.Colors.WHITE,
                        width=300,
                        on_click=criar_escala
                    )
                ], spacing=12),
                padding=ft.padding.all(20),
                expand=True
            )
        ],
        bgcolor=ft.Colors.WHITE
    )
