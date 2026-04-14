"""
api_client.py - Cliente HTTP para comunicar com o backend FastAPI

Centraliza todas as chamadas à API. Assim, se a URL mudar,
só precisamos mudar aqui.

Padrão de uso:
    cliente = APIClient()
    resultado = await cliente.login("email@email.com", "senha")
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")


class APIClient:
    """
    Cliente que faz as chamadas HTTP ao backend.
    Guarda o token JWT após o login.
    """

    def __init__(self):
        self.token: str | None = None
        self.usuario_atual: dict | None = None

    def _cabecalhos(self) -> dict:
        """Retorna os cabeçalhos com o token JWT (se logado)"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    async def login(self, email: str, senha: str) -> dict:
        """
        Faz o login e salva o token.
        Retorna os dados do usuário ou levanta exceção.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "senha": senha}
            )
        if response.status_code == 200:
            dados = response.json()
            self.token = dados["access_token"]
            self.usuario_atual = dados["usuario"]
            return dados
        else:
            erro = response.json().get("detail", "Erro ao fazer login")
            raise Exception(erro)

    async def cadastrar_pastor_e_igreja(self, dados: dict) -> dict:
        """Cadastro inicial: Pastor Presidente + Igreja"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/auth/cadastro-igreja",
                json=dados
            )
        if response.status_code == 201:
            dados_resposta = response.json()
            self.token = dados_resposta["access_token"]
            self.usuario_atual = dados_resposta["usuario"]
            return dados_resposta
        raise Exception(response.json().get("detail", "Erro no cadastro"))

    async def cadastrar_usuario(self, dados: dict, igreja_id: int) -> dict:
        """Cadastra um novo membro/líder"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/auth/cadastro",
                json=dados,
                params={"igreja_id": igreja_id},
                headers=self._cabecalhos()
            )
        if response.status_code == 201:
            return response.json()
        raise Exception(response.json().get("detail", "Erro no cadastro"))

    async def listar_usuarios(self, role: str = None) -> list:
        params = {"role": role} if role else {}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/usuarios",
                params=params,
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro ao listar usuários"))

    async def listar_departamentos(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/departamentos",
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro ao listar departamentos"))

    async def criar_departamento(self, nome: str, descricao: str = None, cor: str = "#3B82F6") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/departamentos",
                json={"nome": nome, "descricao": descricao, "cor": cor},
                headers=self._cabecalhos()
            )
        if response.status_code == 201:
            return response.json()
        raise Exception(response.json().get("detail", "Erro ao criar departamento"))

    async def listar_membros_departamento(self, departamento_id: int) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/departamentos/{departamento_id}/membros",
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def adicionar_membro_departamento(self, departamento_id: int, usuario_id: int, is_lider: bool = False) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/departamentos/{departamento_id}/membros",
                json={"usuario_id": usuario_id, "is_lider": is_lider},
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def listar_dias_culto(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/dias-culto",
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def listar_escalas(self, departamento_id: int = None, mes: int = None, ano: int = None) -> list:
        params = {}
        if departamento_id: params["departamento_id"] = departamento_id
        if mes:             params["mes"] = mes
        if ano:             params["ano"] = ano

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/escalas",
                params=params,
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def criar_escala(self, departamento_id: int, mes: int, ano: int, prazo_limite: str = None) -> dict:
        payload = {"departamento_id": departamento_id, "mes": mes, "ano": ano}
        if prazo_limite:
            payload["prazo_limite"] = prazo_limite

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/escalas",
                json=payload,
                headers=self._cabecalhos()
            )
        if response.status_code == 201:
            return response.json()
        raise Exception(response.json().get("detail", "Erro ao criar escala"))

    async def ver_escala(self, escala_id: int) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/escalas/{escala_id}",
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def adicionar_entrada_escala(self, escala_id: int, usuario_id: int,
                                        dia_culto_id: int, data: str, observacao: str = None) -> dict:
        payload = {
            "usuario_id": usuario_id,
            "dia_culto_id": dia_culto_id,
            "data": data,
            "observacao": observacao
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/escalas/{escala_id}/entradas",
                json=payload,
                headers=self._cabecalhos()
            )
        if response.status_code == 201:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    async def publicar_escala(self, escala_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/escalas/{escala_id}/publicar",
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro ao publicar escala"))

    async def listar_notificacoes(self, apenas_nao_lidas: bool = False) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/notificacoes",
                params={"apenas_nao_lidas": apenas_nao_lidas},
                headers=self._cabecalhos()
            )
        if response.status_code == 200:
            return response.json()
        raise Exception(response.json().get("detail", "Erro"))

    def logout(self):
        """Limpa o token e dados do usuário"""
        self.token = None
        self.usuario_atual = None


# Instância global do cliente (compartilhada entre as páginas)
api = APIClient()
