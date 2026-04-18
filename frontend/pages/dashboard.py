"""
pages/dashboard.py - Tela inicial após o login

Exibe:
- Saudação personalizada com cargo + nome
- Próximos cultos
- Escalas do mês atual
- Notificações não lidas
- Atalhos rápidos (dependendo do role)
"""

import flet as ft
from datetime import date, datetime
from api_client import api

COR_PRIMARIA   = "#1A237E"
COR_SECUNDARIA = "#283593"
COR_DESTAQUE   = "#FFD700"

NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def tela_dashboard(page: ft.Page):
    page.title = "Hineni - Início"

    usuario = api.usuario_atual
    if not usuario:
        page.go("/login")
        return

    nome_display = usuario["nome"].split()[0]
    cargo        = usuario.get("cargo", "")
    role         = usuario.get("role", "MEMBRO")

    hoje = date.today()
    mes_nome = NOMES_MESES[hoje.month]

    # ---- Componentes do dashboard ----

    texto_escalas_loading = ft.Text("Carregando escalas...", color=ft.Colors.GREY_500, italic=True)
    lista_escalas = ft.Column([texto_escalas_loading], spacing=8)

    texto_notif = ft.Text("", color=ft.Colors.GREY_600, size=13, italic=True)
    lista_notif = ft.Column([texto_notif], spacing=8)

    def cartao_escala(escala: dict) -> ft.Container:
        """Cria um cartão para cada escala"""
        status = escala.get("status", "")
        cor_status = {
            "PUBLICADA": ft.Colors.GREEN_700,
            "RASCUNHO":  ft.Colors.ORANGE_700,
            "ARQUIVADA": ft.Colors.GREY_500,
        }.get(status, ft.Colors.GREY_500)

        return ft.Container(
            content=ft.Row([
                ft.Container(width=4, bgcolor=cor_status, border_radius=4),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(
                        f"Mês {escala['mes']}/{escala['ano']}",
                        size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA
                    ),
                    ft.Text(
                        f"{escala['total_entradas']} pessoas escaladas",
                        size=12, color=ft.Colors.GREY_600
                    ),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text(status, size=11, color=cor_status, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.with_opacity(0.1, cor_status),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=ft.padding.all(12),
            border=ft.border.all(1, ft.Colors.GREY_200),
            on_click=lambda e, eid=escala["id"]: page.go(f"/escalas/{eid}"),
            ink=True,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_200, offset=ft.Offset(0, 2))
        )

    def cartao_notificacao(notif: dict) -> ft.Container:
        lida = notif.get("lida", False)
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CIRCLE if not lida else ft.Icons.CIRCLE_OUTLINED,
                    size=10,
                    color=COR_DESTAQUE if not lida else ft.Colors.GREY_400
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(notif["titulo"], size=13, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    ft.Text(
                        notif["mensagem"][:80] + ("..." if len(notif["mensagem"]) > 80 else ""),
                        size=12, color=ft.Colors.GREY_600
                    ),
                ], spacing=2, expand=True),
            ]),
            bgcolor=ft.Colors.WHITE if lida else ft.Colors.BLUE_50,
            border_radius=8,
            padding=ft.padding.all(10),
            border=ft.border.all(1, ft.Colors.GREY_200),
        )

    async def carregar_dados(e=None):
        try:
            # Carrega escalas do mês atual
            escalas = await api.listar_escalas(mes=hoje.month, ano=hoje.year)
            lista_escalas.controls.clear()
            if escalas:
                for escala in escalas[:5]:
                    lista_escalas.controls.append(cartao_escala(escala))
            else:
                lista_escalas.controls.append(
                    ft.Text("Nenhuma escala para este mês", color=ft.Colors.GREY_500, italic=True, size=13)
                )
        except Exception as err:
            lista_escalas.controls = [ft.Text(f"Erro: {err}", color=ft.Colors.RED_400, size=12)]

        try:
            # Carrega notificações não lidas
            notifs = await api.listar_notificacoes(apenas_nao_lidas=True)
            lista_notif.controls.clear()
            if notifs:
                for n in notifs[:3]:
                    lista_notif.controls.append(cartao_notificacao(n))
            else:
                lista_notif.controls.append(
                    ft.Text("Nenhuma notificação nova", color=ft.Colors.GREY_500, italic=True, size=13)
                )
        except Exception as err:
            lista_notif.controls = [ft.Text(f"Erro: {err}", color=ft.Colors.RED_400, size=12)]

        page.update()

    # Atalhos rápidos por role
    def atalho(icone, texto, rota, cor="#1A237E"):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icone, color=ft.Colors.WHITE, size=26),
                    bgcolor=cor,
                    border_radius=12,
                    padding=ft.padding.all(14),
                ),
                ft.Text(texto, size=12, text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_700),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            on_click=lambda e: page.go(rota),
            ink=True,
            border_radius=12,
            padding=ft.padding.all(8),
        )

    atalhos_list = [atalho(ft.Icons.CALENDAR_MONTH, "Escalas", "/escalas", "#1A237E")]
    if role in ("LIDER", "LIDER_MINISTERIO"):
        atalhos_list += [
            atalho(ft.Icons.GROUP_ADD,   "Membros",       "/membros",       "#00897B"),
            atalho(ft.Icons.ADD_CHART,   "Nova Escala",   "/nova-escala",   "#E53935"),
        ]
    if role == "LIDER_MINISTERIO":
        atalhos_list += [
            atalho(ft.Icons.CHURCH,      "Departamentos", "/departamentos", "#6A1B9A"),
            atalho(ft.Icons.EVENT_NOTE,  "Dias de Culto", "/dias_culto",    "#F57C00"),
        ]

    layout = ft.View(
        "/dashboard",
        controls=[
            ft.AppBar(
                title=ft.Text("Hineni", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=COR_PRIMARIA,
                actions=[
                    ft.IconButton(
                        ft.Icons.NOTIFICATIONS,
                        icon_color=ft.Colors.WHITE,
                        on_click=lambda e: page.go("/notificacoes")
                    ),
                    ft.IconButton(
                        ft.Icons.MENU,
                        icon_color=ft.Colors.WHITE,
                        on_click=lambda e: setattr(page.drawer, "open", True) or page.update()
                    ),
                ]
            ),
            ft.Container(
                content=ft.Column([
                    # Saudação
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"Olá, {cargo} {nome_display}! 🙏",
                                size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
                            ),
                            ft.Text(
                                f"{hoje.strftime('%d')} de {mes_nome} de {hoje.year}",
                                size=13, color=ft.Colors.WHITE70
                            ),
                        ], spacing=4),
                        bgcolor=COR_SECUNDARIA,
                        padding=ft.padding.all(20),
                        border_radius=ft.BorderRadius(0, 0, 20, 20),
                    ),

                    ft.Container(height=12),

                    # Atalhos rápidos
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Acesso Rápido", size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                            ft.Container(height=8),
                            ft.Row(atalhos_list, spacing=8, wrap=True),
                        ]),
                        padding=ft.padding.symmetric(horizontal=16)
                    ),

                    ft.Container(height=12),

                    # Escalas do mês
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(
                                    f"Escalas — {mes_nome}/{hoje.year}",
                                    size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA, expand=True
                                ),
                                ft.TextButton(
                                    "Ver todas",
                                    on_click=lambda e: page.go("/escalas"),
                                    style=ft.ButtonStyle(color=COR_SECUNDARIA)
                                )
                            ]),
                            lista_escalas,
                        ]),
                        padding=ft.padding.symmetric(horizontal=16)
                    ),

                    ft.Container(height=12),

                    # Notificações
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(
                                    "Notificações",
                                    size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA, expand=True
                                ),
                                ft.TextButton(
                                    "Ver todas",
                                    on_click=lambda e: page.go("/notificacoes"),
                                    style=ft.ButtonStyle(color=COR_SECUNDARIA)
                                )
                            ]),
                            lista_notif,
                        ]),
                        padding=ft.padding.symmetric(horizontal=16)
                    ),

                    ft.Container(height=20),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=0),
                expand=True,
            )
        ],
        bgcolor=ft.Colors.GREY_50,
        padding=0,
    )

    # Carrega dados ao abrir a tela
    page.run_task(carregar_dados)

    return layout
