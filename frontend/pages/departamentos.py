"""
pages/departamentos.py - Gerenciamento de Departamentos da Igreja

Funcionalidades:
- Lista todos os departamentos ativos
- Seção de "Sugestões" com os departamentos mais comuns (adiciona com 1 clique)
- Criar departamento personalizado (nome, descrição e cor)
- Editar departamento existente
- Desativar departamento (equivale a excluir, mas mantém histórico)
"""

import flet as ft
from api_client import api

COR_PRIMARIA  = "#1A237E"
COR_DESTAQUE  = "#FFD700"

# ── Departamentos sugeridos (os mais comuns em igrejas evangélicas) ──────────
# O líder pode adicionar qualquer um desses com um clique,
# sem precisar digitar nada. Cada um tem uma cor padrão diferente.
SUGESTOES = [
    {"nome": "Obreiros",              "cor": "#1A237E",
     "descricao": "Responsáveis pelo trabalho prático da Igreja"},
    {"nome": "Departamento Infantil", "cor": "#F57F17",
     "descricao": "Ministério dedicado às crianças"},
    {"nome": "Mídia",                 "cor": "#880E4F",
     "descricao": "Redes sociais, fotos e transmissões ao vivo"},
    {"nome": "Som",                   "cor": "#1B5E20",
     "descricao": "Operação e manutenção do sistema de som"},
    {"nome": "Datashow",              "cor": "#4A148C",
     "descricao": "Projeção de letras, slides e apresentações"},
    {"nome": "Abertura / Pregação",   "cor": "#BF360C",
     "descricao": "Ministério de abertura e pregação dos cultos"},
    {"nome": "Cantina",               "cor": "#004D40",
     "descricao": "Preparação e distribuição de lanches e refeições"},
]

# ── Paleta de cores disponíveis para escolher ─────────────────────────────────
PALETA_CORES = [
    "#1A237E", "#283593", "#1565C0", "#0277BD",
    "#00695C", "#1B5E20", "#F57F17", "#E65100",
    "#BF360C", "#880E4F", "#4A148C", "#37474F",
]


def tela_departamentos(page: ft.Page):
    page.title = "Hineni - Departamentos"

    # ── Estado local ──────────────────────────────────────────────────────────
    departamentos: list[dict] = []       # lista carregada da API
    dept_editando: dict | None = None    # departamento sendo editado (None = novo)
    cor_selecionada = {"valor": "#1A237E"}  # dict para mutabilidade dentro das closures

    # ── Componentes do diálogo de criar/editar ────────────────────────────────
    campo_nome    = ft.TextField(label="Nome do departamento *", prefix_icon=ft.Icons.CHURCH, autofocus=True)
    campo_descricao = ft.TextField(
        label="Descrição (opcional)",
        prefix_icon=ft.Icons.DESCRIPTION,
        multiline=True,
        min_lines=2,
        max_lines=3,
    )
    texto_erro_dialog = ft.Text("", color=ft.Colors.RED_600, size=12)
    loading_dialog    = ft.ProgressRing(visible=False, width=18, height=18, color=COR_PRIMARIA)

    # Chips de cor (criados dinamicamente)
    linha_cores = ft.Row(wrap=True, spacing=8)

    def _atualizar_chips_cor(cor_atual: str):
        """Renderiza a paleta de cores, marcando a selecionada com um check."""
        linha_cores.controls.clear()
        for cor in PALETA_CORES:
            selecionada = cor == cor_atual
            linha_cores.controls.append(
                ft.Container(
                    width=32, height=32,
                    bgcolor=cor,
                    border_radius=16,
                    border=ft.border.all(3, ft.Colors.WHITE) if selecionada
                           else ft.border.all(1, ft.Colors.GREY_300),
                    content=ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE, size=16)
                           if selecionada else None,
                    on_click=lambda e, c=cor: _escolher_cor(c),
                    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_400,
                                        offset=ft.Offset(0, 2)) if selecionada else None,
                )
            )
        page.update()

    def _escolher_cor(cor: str):
        cor_selecionada["valor"] = cor
        _atualizar_chips_cor(cor)

    # ── Diálogo de criar / editar ─────────────────────────────────────────────
    dialogo = ft.AlertDialog(modal=True, title=ft.Text("Novo departamento"))

    async def _salvar_departamento(e):
        texto_erro_dialog.value = ""
        nome = campo_nome.value.strip()
        if not nome:
            texto_erro_dialog.value = "O nome é obrigatório"
            page.update()
            return

        loading_dialog.visible = True
        page.update()

        try:
            payload = {
                "nome": nome,
                "descricao": campo_descricao.value.strip() or None,
                "cor": cor_selecionada["valor"],
            }
            if dept_editando:
                await api.atualizar_departamento(dept_editando["id"], payload)
            else:
                await api.criar_departamento(
                    nome=payload["nome"],
                    descricao=payload["descricao"],
                    cor=payload["cor"],
                )
            dialogo.open = False
            await _carregar_departamentos()
        except Exception as err:
            texto_erro_dialog.value = str(err)
        finally:
            loading_dialog.visible = False
            page.update()

    dialogo.content = ft.Container(
        content=ft.Column([
            campo_nome,
            ft.Container(height=4),
            campo_descricao,
            ft.Container(height=8),
            ft.Text("Cor do departamento", size=13, color=ft.Colors.GREY_700),
            ft.Container(height=4),
            linha_cores,
            ft.Container(height=4),
            texto_erro_dialog,
        ], spacing=4, tight=True),
        width=360,
    )
    dialogo.actions = [
        ft.TextButton("Cancelar", on_click=lambda e: _fechar_dialogo()),
        ft.ElevatedButton(
            "Salvar",
            icon=ft.Icons.CHECK,
            bgcolor=COR_PRIMARIA,
            color=ft.Colors.WHITE,
            on_click=_salvar_departamento,
        ),
        loading_dialog,
    ]
    dialogo.actions_alignment = ft.MainAxisAlignment.END

    def _fechar_dialogo():
        dialogo.open = False
        page.update()

    def _abrir_dialogo_novo():
        nonlocal dept_editando
        dept_editando = None
        dialogo.title = ft.Text("Novo departamento")
        campo_nome.value = ""
        campo_descricao.value = ""
        cor_selecionada["valor"] = "#1A237E"
        texto_erro_dialog.value = ""
        _atualizar_chips_cor(cor_selecionada["valor"])
        dialogo.open = True
        page.update()

    def _abrir_dialogo_editar(dept: dict):
        nonlocal dept_editando
        dept_editando = dept
        dialogo.title = ft.Text(f"Editar: {dept['nome']}")
        campo_nome.value = dept["nome"]
        campo_descricao.value = dept.get("descricao") or ""
        cor_selecionada["valor"] = dept.get("cor", "#1A237E")
        texto_erro_dialog.value = ""
        _atualizar_chips_cor(cor_selecionada["valor"])
        dialogo.open = True
        page.update()

    # ── Componentes da tela principal ─────────────────────────────────────────
    lista_principal   = ft.Column(spacing=10)
    secao_sugestoes   = ft.Column(spacing=8, visible=False)
    texto_vazio       = ft.Text(
        "Nenhum departamento criado ainda.",
        color=ft.Colors.GREY_500, italic=True, size=13,
        visible=False,
    )
    loading_principal = ft.ProgressRing(color=COR_PRIMARIA, visible=True)

    def _card_departamento(dept: dict) -> ft.Container:
        """Cartão visual para cada departamento da lista."""
        cor     = dept.get("cor", "#1A237E")
        membros = dept.get("total_membros", 0)
        return ft.Container(
            content=ft.Row([
                # Barra colorida lateral
                ft.Container(width=6, bgcolor=cor, border_radius=ft.BorderRadius(4, 0, 0, 4)),
                ft.Container(width=12),
                # Ícone redondo com a inicial
                ft.Container(
                    content=ft.Text(
                        dept["nome"][0].upper(),
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                    bgcolor=cor,
                    width=40, height=40,
                    border_radius=20,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=12),
                # Nome + descrição + membros
                ft.Column([
                    ft.Text(dept["nome"], size=15, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    ft.Text(
                        dept.get("descricao") or "Sem descrição",
                        size=12, color=ft.Colors.GREY_600,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row([
                        ft.Icon(ft.Icons.PEOPLE, size=13, color=ft.Colors.GREY_500),
                        ft.Text(
                            f"{membros} membro{'s' if membros != 1 else ''}",
                            size=12, color=ft.Colors.GREY_500,
                        ),
                    ], spacing=4),
                ], spacing=2, expand=True),
                # Botão editar
                ft.IconButton(
                    ft.Icons.EDIT_OUTLINED,
                    icon_color=ft.Colors.GREY_500,
                    tooltip="Editar departamento",
                    on_click=lambda e, d=dept: _abrir_dialogo_editar(d),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_200, offset=ft.Offset(0, 2)),
            padding=ft.padding.symmetric(vertical=10),
            ink=True,
        )

    async def _adicionar_sugestao(sugestao: dict):
        """Cria um departamento sugerido com um clique."""
        try:
            await api.criar_departamento(
                nome=sugestao["nome"],
                descricao=sugestao["descricao"],
                cor=sugestao["cor"],
            )
            await _carregar_departamentos()
        except Exception as err:
            # Nome duplicado é possível — ignora silenciosamente
            # (o usuário pode ter adicionado antes)
            if "já existe" not in str(err).lower():
                pass   # Outro erro — ignora para não travar a tela

    def _chip_sugestao(s: dict, ja_existe: bool) -> ft.Container:
        """
        Chip clicável para departamentos sugeridos.
        Se já foi criado, aparece em verde com ✓. Senão, aparece como botão.
        """
        if ja_existe:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(s["nome"], size=13, color=ft.Colors.GREEN_700),
                ], spacing=6, tight=True),
                bgcolor=ft.Colors.GREEN_50,
                border=ft.border.all(1, ft.Colors.GREEN_300),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
            )
        return ft.Container(
            content=ft.Row([
                ft.Container(width=14, height=14, bgcolor=s["cor"], border_radius=7),
                ft.Text(s["nome"], size=13, color=ft.Colors.GREY_800),
                ft.Icon(ft.Icons.ADD, size=14, color=ft.Colors.GREY_600),
            ], spacing=6, tight=True),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda e, dep=s: page.run_task(_adicionar_sugestao, dep),
        )

    async def _carregar_departamentos(e=None):
        """Busca os departamentos da API e atualiza a tela."""
        nonlocal departamentos
        loading_principal.visible = True
        lista_principal.controls.clear()
        secao_sugestoes.controls.clear()
        page.update()

        try:
            departamentos = await api.listar_departamentos()
        except Exception as err:
            lista_principal.controls.append(
                ft.Text(f"Erro ao carregar: {err}", color=ft.Colors.RED_400, size=13)
            )
            loading_principal.visible = False
            page.update()
            return

        loading_principal.visible = False
        nomes_existentes = {d["nome"] for d in departamentos}

        # ── Seção de sugestões ────────────────────────────────────────────
        # Só aparece se ainda existe alguma sugestão não adicionada,
        # ou se a lista estiver vazia (para ajudar o usuário a começar).
        sugestoes_pendentes = [s for s in SUGESTOES if s["nome"] not in nomes_existentes]
        if sugestoes_pendentes:
            secao_sugestoes.visible = True
            secao_sugestoes.controls = [
                ft.Text(
                    "Departamentos sugeridos" if departamentos else "Por onde começar?",
                    size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA,
                ),
                ft.Text(
                    "Toque para adicionar com um clique:",
                    size=12, color=ft.Colors.GREY_600, italic=True,
                ),
                ft.Row(
                    controls=[_chip_sugestao(s, s["nome"] in nomes_existentes) for s in SUGESTOES],
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                ),
            ]
        else:
            secao_sugestoes.visible = False

        # ── Lista de departamentos criados ────────────────────────────────
        if departamentos:
            texto_vazio.visible = False
            for dept in departamentos:
                lista_principal.controls.append(_card_departamento(dept))
        else:
            texto_vazio.visible = True

        page.update()

    # Registra o diálogo na página
    page.overlay.append(dialogo)

    # Carrega os dados ao abrir a tela
    page.run_task(_carregar_departamentos)

    return ft.View(
        "/departamentos",
        controls=[
            ft.AppBar(
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda e: page.go("/dashboard"),
                ),
                title=ft.Text("Departamentos", color=ft.Colors.WHITE),
                bgcolor=COR_PRIMARIA,
                actions=[
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Atualizar",
                        on_click=lambda e: page.run_task(_carregar_departamentos),
                    ),
                ],
            ),
            ft.Container(
                content=ft.Column([

                    # ── Sugestões ─────────────────────────────────────────
                    ft.Container(
                        content=secao_sugestoes,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=12,
                        padding=ft.padding.all(16),
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                    ),

                    # ── Cabeçalho da lista ────────────────────────────────
                    ft.Row([
                        ft.Text(
                            "Seus departamentos",
                            size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA,
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Novo",
                            icon=ft.Icons.ADD,
                            bgcolor=COR_PRIMARIA,
                            color=ft.Colors.WHITE,
                            on_click=lambda e: _abrir_dialogo_novo(),
                        ),
                    ]),

                    # ── Loading / lista / texto vazio ─────────────────────
                    loading_principal,
                    texto_vazio,
                    lista_principal,

                    ft.Container(height=80),   # Espaço extra no final
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.all(16),
                expand=True,
            ),
        ],
        bgcolor=ft.Colors.GREY_50,
        padding=0,
    )
