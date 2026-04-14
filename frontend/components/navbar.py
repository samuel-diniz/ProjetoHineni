"""
components/navbar.py - Barra de navegação lateral

Componente reutilizável que aparece em todas as telas após o login.
Mostra opções diferentes dependendo do role do usuário.
"""

import flet as ft
from api_client import api


def criar_navbar(page: ft.Page, pagina_ativa: str = "dashboard"):
    """
    Cria a barra de navegação lateral (menu).

    pagina_ativa: nome da página atual (para destacar no menu)
    """
    usuario = api.usuario_atual
    if not usuario:
        return ft.Container()

    role = usuario.get("role", "MEMBRO")
    nome = usuario.get("nome", "Usuário")
    cargo = usuario.get("cargo", "")

    # Cor principal do app
    COR_PRIMARIA   = "#1A237E"   # Azul escuro
    COR_SECUNDARIA = "#283593"
    COR_DESTAQUE   = "#FFD700"   # Dourado

    def item_menu(icone, texto, pagina_destino):
        """Cria um item clicável do menu"""
        ativo = pagina_ativa == pagina_destino
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    icone,
                    color=COR_DESTAQUE if ativo else ft.Colors.WHITE70,
                    size=20
                ),
                ft.Text(
                    texto,
                    color=COR_DESTAQUE if ativo else ft.Colors.WHITE70,
                    size=14,
                    weight=ft.FontWeight.BOLD if ativo else ft.FontWeight.NORMAL
                )
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.15, COR_DESTAQUE) if ativo else None,
            on_click=lambda e, p=pagina_destino: navegar(page, p),
            ink=True,
        )

    # Itens disponíveis para todos
    itens = [
        item_menu(ft.Icons.DASHBOARD, "Início", "dashboard"),
        item_menu(ft.Icons.CALENDAR_MONTH, "Escalas", "escalas"),
        item_menu(ft.Icons.NOTIFICATIONS, "Notificações", "notificacoes"),
    ]

    # Itens apenas para Líder e Pastor
    if role in ("LIDER", "PASTOR_PRESIDENTE"):
        itens.insert(2, item_menu(ft.Icons.GROUP, "Membros", "membros"))
        itens.insert(3, item_menu(ft.Icons.CHURCH, "Departamentos", "departamentos"))

    # Itens apenas para Pastor Presidente
    if role == "PASTOR_PRESIDENTE":
        itens.append(item_menu(ft.Icons.SETTINGS, "Configurações", "configuracoes"))
        itens.append(item_menu(ft.Icons.EVENT, "Dias de Culto", "dias_culto"))

    def navegar(page, destino):
        page.go(f"/{destino}")

    def fazer_logout(e):
        api.logout()
        page.go("/login")

    return ft.NavigationDrawer(
        controls=[
            # Cabeçalho com info do usuário
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=60, color=ft.Colors.WHITE),
                    ft.Text(nome, color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(cargo, color=ft.Colors.WHITE60, size=12),
                    ft.Container(height=20),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COR_PRIMARIA,
                padding=ft.padding.symmetric(vertical=10)
            ),

            ft.Divider(height=1, color=ft.Colors.WHITE24),
            ft.Container(height=8),

            # Itens do menu
            *itens,

            # Spacer + Logout no final
            ft.Container(expand=True),
            ft.Divider(height=1, color=ft.Colors.WHITE24),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_300, size=20),
                    ft.Text("Sair", color=ft.Colors.RED_300, size=14)
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                on_click=fazer_logout,
                ink=True,
            ),
            ft.Container(height=8),
        ],
        bgcolor=COR_SECUNDARIA,
    )
