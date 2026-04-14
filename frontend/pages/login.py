"""
pages/login.py - Tela de Login e Cadastro Inicial

Duas telas neste arquivo:
1. Tela de Login (e-mail + senha)
2. Tela de Cadastro Inicial (Pastor Presidente + Igreja) - exibida no primeiro uso
"""

import flet as ft
from api_client import api


COR_PRIMARIA   = "#1A237E"
COR_SECUNDARIA = "#283593"
COR_DESTAQUE   = "#FFD700"


def tela_login(page: ft.Page):
    """Tela principal de login"""
    page.title = "Hineni - Login"
    page.bgcolor = COR_PRIMARIA

    campo_email = ft.TextField(
        label="E-mail",
        border_color=ft.Colors.WHITE54,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70),
        color=ft.Colors.WHITE,
        prefix_icon=ft.Icons.EMAIL,
        keyboard_type=ft.KeyboardType.EMAIL,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )
    campo_senha = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        border_color=ft.Colors.WHITE54,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70),
        color=ft.Colors.WHITE,
        prefix_icon=ft.Icons.LOCK,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )
    texto_erro = ft.Text("", color=ft.Colors.RED_300, size=13)
    btn_entrar = ft.ElevatedButton(
        "ENTRAR",
        icon=ft.Icons.LOGIN,
        style=ft.ButtonStyle(
            bgcolor=COR_DESTAQUE,
            color=COR_PRIMARIA,
            padding=ft.padding.symmetric(horizontal=40, vertical=14),
            text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
        ),
        width=300,
    )
    loading = ft.ProgressRing(visible=False, color=COR_DESTAQUE)

    async def fazer_login(e):
        texto_erro.value = ""
        email = campo_email.value.strip()
        senha = campo_senha.value

        if not email or not senha:
            texto_erro.value = "Preencha e-mail e senha"
            page.update()
            return

        btn_entrar.disabled = True
        loading.visible = True
        page.update()

        try:
            await api.login(email, senha)
            page.go("/dashboard")
        except Exception as erro:
            texto_erro.value = str(erro)
        finally:
            btn_entrar.disabled = False
            loading.visible = False
            page.update()

    btn_entrar.on_click = fazer_login
    campo_senha.on_submit = fazer_login

    return ft.View(
        "/login",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Container(height=40),

                    # Logo / Título
                    ft.Column([
                        ft.Icon(ft.Icons.CHURCH, size=70, color=COR_DESTAQUE),
                        ft.Text(
                            "HINENI",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            letter_spacing=6
                        ),
                        ft.Text(
                            "Sistema de Escalas da Igreja",
                            size=14,
                            color=ft.Colors.WHITE70,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),

                    ft.Container(height=40),

                    # Card de login
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Entrar", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(height=16),
                            campo_email,
                            ft.Container(height=8),
                            campo_senha,
                            ft.Container(height=8),
                            texto_erro,
                            ft.Container(height=16),
                            ft.Row([loading, btn_entrar], alignment=ft.MainAxisAlignment.CENTER),
                        ], spacing=0),
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        border_radius=16,
                        padding=ft.padding.all(28),
                        width=350,
                    ),

                    ft.Container(height=20),
                    ft.TextButton(
                        "Primeiro acesso? Cadastre sua Igreja",
                        style=ft.ButtonStyle(color=COR_DESTAQUE),
                        on_click=lambda e: page.go("/cadastro-inicial")
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                alignment=ft.alignment.center,
            )
        ],
        bgcolor=COR_PRIMARIA,
        padding=0,
    )


def tela_cadastro_inicial(page: ft.Page):
    """Tela de cadastro do Pastor Presidente + Igreja (primeiro uso)"""
    page.title = "Hineni - Cadastro Inicial"

    # Campos da Igreja
    campo_nome_igreja = ft.TextField(label="Nome da Igreja *", prefix_icon=ft.Icons.CHURCH)
    campo_endereco    = ft.TextField(label="Endereço (opcional)", prefix_icon=ft.Icons.LOCATION_ON)

    # Campos do Pastor
    campo_nome    = ft.TextField(label="Seu nome completo *", prefix_icon=ft.Icons.PERSON)
    campo_email   = ft.TextField(label="E-mail *", keyboard_type=ft.KeyboardType.EMAIL, prefix_icon=ft.Icons.EMAIL)
    campo_tel     = ft.TextField(label="WhatsApp (com DDD) *", keyboard_type=ft.KeyboardType.PHONE, prefix_icon=ft.Icons.PHONE)
    campo_senha   = ft.TextField(label="Senha (mín. 6 caracteres) *", password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)

    dropdown_genero = ft.Dropdown(
        label="Gênero *",
        options=[
            ft.dropdown.Option("MASCULINO", "Masculino"),
            ft.dropdown.Option("FEMININO", "Feminino"),
        ],
        value="MASCULINO"
    )

    dropdown_cargo = ft.Dropdown(
        label="Cargo *",
        options=[ft.dropdown.Option("Pastor", "Pastor")],
        value="Pastor"
    )

    def atualizar_cargos(e):
        genero = dropdown_genero.value
        if genero == "MASCULINO":
            dropdown_cargo.options = [
                ft.dropdown.Option("Pastor", "Pastor"),
                ft.dropdown.Option("Presbítero", "Presbítero"),
                ft.dropdown.Option("Evangelista", "Evangelista"),
            ]
            dropdown_cargo.value = "Pastor"
        else:
            dropdown_cargo.options = [
                ft.dropdown.Option("Pastora", "Pastora"),
                ft.dropdown.Option("Missionária", "Missionária"),
            ]
            dropdown_cargo.value = "Pastora"
        page.update()

    dropdown_genero.on_change = atualizar_cargos

    texto_erro = ft.Text("", color=ft.Colors.RED_600, size=13)
    btn_cadastrar = ft.ElevatedButton(
        "CADASTRAR",
        icon=ft.Icons.CHECK_CIRCLE,
        bgcolor=COR_PRIMARIA,
        color=ft.Colors.WHITE,
        width=300,
    )

    async def cadastrar(e):
        texto_erro.value = ""

        # Validação básica
        campos_obrigatorios = [
            (campo_nome_igreja, "nome da Igreja"),
            (campo_nome, "seu nome"),
            (campo_email, "e-mail"),
            (campo_tel, "WhatsApp"),
            (campo_senha, "senha"),
        ]
        for campo, nome in campos_obrigatorios:
            if not campo.value or not campo.value.strip():
                texto_erro.value = f"O campo '{nome}' é obrigatório"
                page.update()
                return

        if len(campo_senha.value) < 6:
            texto_erro.value = "A senha deve ter no mínimo 6 caracteres"
            page.update()
            return

        btn_cadastrar.disabled = True
        page.update()

        try:
            dados = {
                "nome": campo_nome.value.strip(),
                "email": campo_email.value.strip(),
                "telefone": campo_tel.value.strip(),
                "senha": campo_senha.value,
                "genero": dropdown_genero.value,
                "cargo": dropdown_cargo.value,
                "role": "PASTOR_PRESIDENTE",
                "igreja": {
                    "nome": campo_nome_igreja.value.strip(),
                    "endereco": campo_endereco.value.strip() or None,
                }
            }
            await api.cadastrar_pastor_e_igreja(dados)
            page.go("/dashboard")
        except Exception as erro:
            texto_erro.value = str(erro)
        finally:
            btn_cadastrar.disabled = False
            page.update()

    btn_cadastrar.on_click = cadastrar

    return ft.View(
        "/cadastro-inicial",
        controls=[
            ft.AppBar(
                title=ft.Text("Cadastro Inicial"),
                bgcolor=COR_PRIMARIA,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda e: page.go("/login")
                )
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Sua Igreja", size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    campo_nome_igreja,
                    campo_endereco,

                    ft.Divider(height=20),
                    ft.Text("Dados do Pastor Presidente", size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    campo_nome,
                    campo_email,
                    campo_tel,
                    campo_senha,
                    ft.Row([dropdown_genero, dropdown_cargo], spacing=16),

                    ft.Container(height=8),
                    texto_erro,
                    ft.Row([btn_cadastrar], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                ], spacing=12, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.all(20),
                expand=True,
            )
        ],
        bgcolor=ft.Colors.WHITE,
    )
