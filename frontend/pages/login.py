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
                            style=ft.TextStyle(letter_spacing=6),
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
    """Tela de cadastro do Líder do Ministério + Igreja (primeiro uso)"""
    page.title = "Hineni - Cadastro Inicial"
    import re

    # ---- Campos da Igreja ----
    campo_cnpj        = ft.TextField(
        label="CNPJ da Igreja *",
        hint_text="Digite os 14 números",
        prefix_icon=ft.Icons.BUSINESS,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    campo_nome_igreja = ft.TextField(label="Nome da Igreja *", prefix_icon=ft.Icons.CHURCH)
    campo_cpf         = ft.TextField(
        label="CPF do Líder *",
        hint_text="Digite os 11 números",
        prefix_icon=ft.Icons.BADGE,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    campo_cep         = ft.TextField(
        label="CEP *",
        hint_text="Digite os 8 números",
        prefix_icon=ft.Icons.LOCATION_ON,
        keyboard_type=ft.KeyboardType.NUMBER,
        width=160,
    )
    campo_logradouro  = ft.TextField(
        label="Logradouro *",
        hint_text="Avenida Paulista",
        prefix_icon=ft.Icons.MAP,
        expand=True,
    )
    aviso_logradouro = ft.Text(
        "",
        size=11,
        color=ft.Colors.ORANGE_700,
        italic=True,
        visible=False,
    )
    campo_numero      = ft.TextField(
        label="Número",
        hint_text="1578",
        prefix_icon=ft.Icons.LABEL,
        width=110,
    )
    campo_complemento = ft.TextField(
        label="Complemento",
        hint_text="Sala 3, Apto 12…",
        prefix_icon=ft.Icons.EDIT,
        width=200,
    )
    campo_bairro      = ft.TextField(
        label="Bairro *",
        hint_text="Centro",
        prefix_icon=ft.Icons.LOCATION_CITY,
        expand=True,
    )
    campo_cidade      = ft.TextField(
        label="Cidade *",
        hint_text="São Paulo",
        prefix_icon=ft.Icons.LOCATION_ON,
        expand=True,
    )
    campo_uf          = ft.TextField(
        label="UF *",
        hint_text="SP",
        prefix_icon=ft.Icons.PUBLIC,
        width=80,
        max_length=2,
        capitalization=ft.TextCapitalization.CHARACTERS,
    )
    campo_tel_igreja  = ft.TextField(
        label="Telefone da Igreja (opcional)",
        prefix_icon=ft.Icons.PHONE,
        keyboard_type=ft.KeyboardType.PHONE,
    )

    texto_cnpj_status = ft.Text("", size=12, italic=True)
    loading_cnpj      = ft.ProgressRing(visible=False, width=16, height=16, color=COR_PRIMARIA)

    # ---- Campos do Líder do Ministério ----
    campo_nome  = ft.TextField(label="Seu nome completo *", prefix_icon=ft.Icons.PERSON)
    campo_email = ft.TextField(label="E-mail *", keyboard_type=ft.KeyboardType.EMAIL, prefix_icon=ft.Icons.EMAIL)
    campo_tel   = ft.TextField(label="WhatsApp (com DDD) *", keyboard_type=ft.KeyboardType.PHONE, prefix_icon=ft.Icons.PHONE)
    campo_senha = ft.TextField(label="Senha (mín. 6 caracteres) *", password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)

    dropdown_genero = ft.Dropdown(
        label="Gênero *",
        options=[
            ft.dropdown.Option("MASCULINO", "Masculino"),
            ft.dropdown.Option("FEMININO", "Feminino"),
        ],
        value="MASCULINO",
        width=180,
    )
    dropdown_cargo = ft.Dropdown(
        label="Cargo *",
        options=[
            ft.dropdown.Option("Pastor", "Pastor"),
            ft.dropdown.Option("Bispo", "Bispo"),
            ft.dropdown.Option("Apóstolo", "Apóstolo"),
            ft.dropdown.Option("Presbítero", "Presbítero"),
            ft.dropdown.Option("Evangelista", "Evangelista"),
        ],
        value="Pastor",
        expand=True,
    )

    def atualizar_cargos(e):
        if dropdown_genero.value == "MASCULINO":
            dropdown_cargo.options = [
                ft.dropdown.Option("Pastor", "Pastor"),
                ft.dropdown.Option("Bispo", "Bispo"),
                ft.dropdown.Option("Apóstolo", "Apóstolo"),
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

    # ---- Tipos de logradouro reconhecidos no Brasil ----
    _TIPOS_LOGRADOURO = {
        "rua", "avenida", "av", "alameda", "al", "travessa", "tv",
        "rodovia", "estrada", "praça", "largo", "beco", "viela",
        "quadra", "setor", "condomínio", "fazenda", "sitio", "sítio",
        "vila", "parque", "jardim", "conjunto", "residencial",
    }

    def _verificar_tipo_logradouro(valor: str):
        """
        Verifica se o logradouro começa com um tipo reconhecido.
        Se não, exibe um aviso pedindo ao usuário para completar.
        """
        if not valor:
            aviso_logradouro.visible = False
            return
        primeira_palavra = valor.strip().split()[0].lower().rstrip(".")
        if primeira_palavra not in _TIPOS_LOGRADOURO:
            aviso_logradouro.value = (
                "⚠ Os Correios não informaram o tipo deste logradouro. "
                "Adicione manualmente: Rua, Avenida, Alameda, etc."
            )
            aviso_logradouro.visible = True
        else:
            aviso_logradouro.visible = False

    # ---- Limpeza no on_change: só dígitos, limite de tamanho ----
    # Lógica: on_change remove não-dígitos e corta no máximo permitido.
    # SÓ atualiza o campo se algo mudou → evita loop de cursor.
    # on_blur faz a formatação visual (pontos, traço, barra).

    def _so_digitos(valor: str, limite: int) -> str:
        """Retorna apenas os dígitos do valor, até o limite."""
        return re.sub(r'\D', '', valor or "")[:limite]

    def on_cnpj_change(e):
        limpo = _so_digitos(campo_cnpj.value, 14)
        if campo_cnpj.value != limpo:
            campo_cnpj.value = limpo
            page.update()

    def on_cpf_change(e):
        limpo = _so_digitos(campo_cpf.value, 11)
        if campo_cpf.value != limpo:
            campo_cpf.value = limpo
            page.update()

    def on_cep_change(e):
        limpo = _so_digitos(campo_cep.value, 8)
        if campo_cep.value != limpo:
            campo_cep.value = limpo
            page.update()

    campo_cnpj.on_change = on_cnpj_change
    campo_cpf.on_change  = on_cpf_change
    campo_cep.on_change  = on_cep_change

    # ---- Funções de formatação (aplicadas só no on_blur) ----

    def _fmt_cnpj(valor: str) -> str:
        n = _so_digitos(valor, 14)
        if len(n) < 14:
            return n
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"

    def _fmt_cep(valor: str) -> str:
        n = _so_digitos(valor, 8)
        if len(n) < 8:
            return n
        return f"{n[:5]}-{n[5:]}"

    def _fmt_cpf(valor: str) -> str:
        n = _so_digitos(valor, 11)
        if len(n) < 11:
            return n
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"

    def on_cpf_blur(e):
        campo_cpf.value = _fmt_cpf(campo_cpf.value or "")
        page.update()

    campo_cpf.on_blur = on_cpf_blur

    # ---- Auto-fill ao sair do campo CNPJ ----
    async def buscar_dados_cnpj(e):
        cnpj = _so_digitos(campo_cnpj.value, 14)
        # Formata visualmente antes de consultar
        campo_cnpj.value = _fmt_cnpj(cnpj)
        page.update()

        if len(cnpj) != 14:
            return

        loading_cnpj.visible = True
        texto_cnpj_status.value = "Consultando CNPJ..."
        texto_cnpj_status.color = ft.Colors.GREY_600
        page.update()

        try:
            async with __import__('httpx').AsyncClient(timeout=10) as client:
                resp = await client.get(f"http://localhost:8000/consulta/cnpj/{cnpj}")

            if resp.status_code == 200:
                dados = resp.json()
                # Preenche cada campo separadamente — só se ainda estiver vazio

                nome_sugerido = dados.get("nome_fantasia") or dados.get("razao_social", "")
                if nome_sugerido and not campo_nome_igreja.value:
                    campo_nome_igreja.value = nome_sugerido

                # CEP: guarda só os dígitos (o on_blur vai formatar para 00000-000)
                if dados.get("cep") and not campo_cep.value:
                    campo_cep.value = _so_digitos(dados["cep"], 8)

                # Logradouro: "Avenida Conselheiro Carrão" (só a rua, sem número/bairro)
                if dados.get("logradouro") and not campo_logradouro.value:
                    campo_logradouro.value = dados["logradouro"]
                _verificar_tipo_logradouro(campo_logradouro.value)

                # Número do endereço
                if dados.get("numero") and not campo_numero.value:
                    campo_numero.value = dados["numero"]

                # Complemento (nem sempre vem preenchido)
                if dados.get("complemento") and not campo_complemento.value:
                    campo_complemento.value = dados["complemento"]

                # Bairro (agora vem separado no schema DadosCNPJ)
                if dados.get("bairro") and not campo_bairro.value:
                    campo_bairro.value = dados["bairro"]

                # Cidade e UF
                if dados.get("municipio") and not campo_cidade.value:
                    campo_cidade.value = dados["municipio"]
                if dados.get("uf") and not campo_uf.value:
                    campo_uf.value = dados["uf"]

                # Telefone
                if dados.get("telefone") and not campo_tel_igreja.value:
                    campo_tel_igreja.value = dados["telefone"]

                situacao = dados.get("situacao_cadastral", "")
                if situacao and situacao.upper() != "ATIVA":
                    texto_cnpj_status.value = f"⚠ Situação: {situacao}"
                    texto_cnpj_status.color = ft.Colors.ORANGE_700
                else:
                    texto_cnpj_status.value = "✓ CNPJ válido e ativo"
                    texto_cnpj_status.color = ft.Colors.GREEN_700
            elif resp.status_code == 404:
                texto_cnpj_status.value = "CNPJ não encontrado na Receita Federal"
                texto_cnpj_status.color = ft.Colors.RED_600
            else:
                erro = resp.json().get("detail", "Erro na consulta")
                texto_cnpj_status.value = f"✗ {erro}"
                texto_cnpj_status.color = ft.Colors.RED_600
        except Exception as err:
            texto_cnpj_status.value = f"Sem conexão para validar CNPJ: {err}"
            texto_cnpj_status.color = ft.Colors.ORANGE_700

        loading_cnpj.visible = False
        page.update()

    campo_cnpj.on_blur = buscar_dados_cnpj

    # ---- Auto-fill ao sair do campo CEP ----
    async def buscar_endereco_cep(e):
        cep = _so_digitos(campo_cep.value, 8)
        campo_cep.value = _fmt_cep(cep)
        page.update()

        if len(cep) != 8:
            return
        try:
            async with __import__('httpx').AsyncClient(timeout=8) as client:
                resp = await client.get(f"http://localhost:8000/consulta/cep/{cep}")
            if resp.status_code == 200:
                dados = resp.json()
                # Preenche apenas campos ainda vazios
                if dados.get("logradouro") and not campo_logradouro.value:
                    campo_logradouro.value = dados["logradouro"]
                if dados.get("complemento") and not campo_complemento.value:
                    campo_complemento.value = dados["complemento"]
                if dados.get("bairro") and not campo_bairro.value:
                    campo_bairro.value = dados["bairro"]
                if dados.get("municipio") and not campo_cidade.value:
                    campo_cidade.value = dados["municipio"]
                if dados.get("uf") and not campo_uf.value:
                    campo_uf.value = dados["uf"]
                # Avisa se o tipo do logradouro estiver faltando
                _verificar_tipo_logradouro(campo_logradouro.value)
                page.update()
        except Exception:
            pass

    campo_cep.on_blur = buscar_endereco_cep

    texto_erro = ft.Text("", color=ft.Colors.RED_600, size=13)
    btn_cadastrar = ft.ElevatedButton(
        "CADASTRAR",
        icon=ft.Icons.CHECK_CIRCLE,
        bgcolor=COR_PRIMARIA,
        color=ft.Colors.WHITE,
        width=320,
    )

    async def cadastrar(e):
        texto_erro.value = ""

        campos_obrigatorios = [
            (campo_cnpj,        "CNPJ da Igreja"),
            (campo_nome_igreja, "Nome da Igreja"),
            (campo_cep,         "CEP"),
            (campo_logradouro,  "Logradouro"),
            (campo_bairro,      "Bairro"),
            (campo_cidade,      "Cidade"),
            (campo_uf,          "UF"),
            (campo_nome,        "seu nome"),
            (campo_cpf,         "CPF"),
            (campo_email,       "e-mail"),
            (campo_tel,         "WhatsApp"),
            (campo_senha,       "senha"),
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
                "cpf": campo_cpf.value.strip() or None,
                "email": campo_email.value.strip(),
                "telefone": campo_tel.value.strip(),
                "senha": campo_senha.value,
                "genero": dropdown_genero.value,
                "cargo": dropdown_cargo.value,
                "role": "LIDER_MINISTERIO",
                "igreja": {
                    "nome":        campo_nome_igreja.value.strip(),
                    "cnpj":        campo_cnpj.value.strip(),
                    "cep":         campo_cep.value.strip(),
                    "logradouro":  campo_logradouro.value.strip(),
                    "numero":      campo_numero.value.strip() or None,
                    "complemento": campo_complemento.value.strip() or None,
                    "bairro":      campo_bairro.value.strip(),
                    "cidade":      campo_cidade.value.strip(),
                    "uf":          campo_uf.value.strip().upper(),
                    "telefone":    campo_tel_igreja.value.strip() or None,
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
                title=ft.Text("Cadastro Inicial — Líder do Ministério"),
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
                    # ---- Seção Igreja ----
                    ft.Text("Dados da Igreja", size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),

                    # CNPJ com status de validação
                    campo_cnpj,
                    ft.Row([loading_cnpj, texto_cnpj_status], spacing=6),

                    campo_nome_igreja,
                    campo_tel_igreja,

                    # CEP (ao sair, preenche os campos abaixo automaticamente)
                    campo_cep,

                    # Logradouro ocupa toda a largura
                    campo_logradouro,
                    aviso_logradouro,

                    # Número + Complemento na mesma linha
                    ft.Row([campo_numero, campo_complemento], spacing=12),

                    # Bairro + Cidade + UF na mesma linha
                    ft.Row([campo_bairro, campo_cidade, campo_uf], spacing=12),

                    ft.Divider(height=20),

                    # ---- Seção Líder ----
                    ft.Text("Dados do Líder do Ministério", size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    campo_nome,
                    campo_cpf,
                    campo_email,
                    campo_tel,
                    campo_senha,
                    ft.Row([dropdown_genero, dropdown_cargo], spacing=12),

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
