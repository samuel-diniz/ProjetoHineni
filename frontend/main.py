"""
main.py - Entrada do aplicativo Flet (Frontend)

Este arquivo:
1. Inicializa o app Flet
2. Configura o roteamento (qual tela mostrar para qual URL)
3. Define o tema visual do app

Para rodar:
    cd frontend
    flet run main.py          # Desktop
    flet run --web main.py    # Web (navegador)
    flet run --android main.py  # Android (requer dispositivo)
"""

import flet as ft
from pages.login import tela_login, tela_cadastro_inicial
from pages.dashboard import tela_dashboard
from pages.escalas import tela_lista_escalas, tela_nova_escala
from api_client import api


def main(page: ft.Page):
    """Função principal do app - configura e inicializa tudo"""

    # ---- Configurações globais da página ----
    page.title = "Hineni - Sistema de Escalas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "Roboto": "https://fonts.gstatic.com/s/roboto/v32/KFOmCnqEu92Fr1Me5Q.ttf"
    }
    page.theme = ft.Theme(
        color_scheme_seed="#1A237E",
        font_family="Roboto",
    )

    # No celular, remove a barra de padding superior
    page.padding = 0

    # ---- Roteamento ----
    def rota_mudou(e: ft.RouteChangeEvent):
        """
        Chamado toda vez que a URL/rota muda.
        Aqui decidimos qual tela mostrar.
        """
        page.views.clear()

        rota = page.route

        # Rotas públicas (sem login)
        if rota == "/login" or rota == "/":
            page.views.append(tela_login(page))

        elif rota == "/cadastro-inicial":
            page.views.append(tela_cadastro_inicial(page))

        # Rotas protegidas (precisa estar logado)
        elif rota == "/dashboard":
            if not api.token:
                page.go("/login")
                return
            page.views.append(tela_dashboard(page))

        elif rota == "/escalas":
            if not api.token:
                page.go("/login")
                return
            page.views.append(tela_lista_escalas(page))

        elif rota == "/nova-escala":
            if not api.token:
                page.go("/login")
                return
            page.views.append(tela_nova_escala(page))

        else:
            # Rota não encontrada - volta para o início
            page.go("/login" if not api.token else "/dashboard")
            return

        page.update()

    def pop_view(e: ft.ViewPopEvent):
        """Chamado quando o usuário pressiona o botão Voltar"""
        page.views.pop()
        topo = page.views[-1]
        page.go(topo.route)

    page.on_route_change = rota_mudou
    page.on_view_pop     = pop_view

    # Rota inicial
    page.go("/login" if not api.token else "/dashboard")


# Inicia o app
if __name__ == "__main__":
    ft.app(
        target=main,
        # Para rodar no navegador, use: ft.app(target=main, view=ft.AppView.WEB_BROWSER)
        # Para rodar como desktop: ft.app(target=main)
        view=ft.AppView.WEB_BROWSER,
        port=8550,
    )
