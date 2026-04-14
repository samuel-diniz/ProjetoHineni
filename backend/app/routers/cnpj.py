"""
routers/cnpj.py - Consulta de CNPJ via BrasilAPI e CEP via ViaCEP

Rotas:
  GET /cnpj/{cnpj}   → Busca dados da empresa pelo CNPJ (BrasilAPI - grátis, sem auth)
  GET /cep/{cep}     → Busca endereço pelo CEP (ViaCEP - grátis, sem auth)

Usado no cadastro da Igreja para preencher automaticamente os campos.
"""

import re
import httpx
from fastapi import APIRouter, HTTPException, status
from app.schemas import DadosCNPJ

router = APIRouter(prefix="/consulta", tags=["Consulta CNPJ/CEP"])

BRASIL_API_URL     = "https://brasilapi.com.br/api/cnpj/v1"
BRASIL_API_CEP_URL = "https://brasilapi.com.br/api/cep/v2"
VIACEP_URL         = "https://viacep.com.br/ws"


def _limpar_cnpj(cnpj: str) -> str:
    """Remove formatação do CNPJ, deixa só números"""
    return re.sub(r'\D', '', cnpj)


def _validar_algoritmo_cnpj(cnpj: str) -> bool:
    """Valida os dígitos verificadores do CNPJ"""
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    if int(cnpj[12]) != (0 if resto < 2 else 11 - resto):
        return False

    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    return int(cnpj[13]) == (0 if resto < 2 else 11 - resto)


@router.get(
    "/cnpj/{cnpj}",
    response_model=DadosCNPJ,
    summary="Consultar dados pelo CNPJ"
)
async def consultar_cnpj(cnpj: str):
    """
    Busca os dados cadastrais de uma empresa pelo CNPJ.
    Usa a BrasilAPI (gratuita, sem necessidade de cadastro).

    Exemplo: GET /consulta/cnpj/04222355000148
    """
    cnpj_limpo = _limpar_cnpj(cnpj)

    # Valida formato e algoritmo antes de consultar
    if len(cnpj_limpo) != 14:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ deve ter 14 dígitos"
        )
    if not _validar_algoritmo_cnpj(cnpj_limpo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ inválido — dígitos verificadores incorretos"
        )

    # Consulta a BrasilAPI
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BRASIL_API_URL}/{cnpj_limpo}")
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Timeout ao consultar CNPJ — tente novamente"
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CNPJ não encontrado na Receita Federal"
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao consultar CNPJ — serviço externo indisponível"
        )

    dados = response.json()

    # A BrasilAPI separa o tipo ("AVENIDA", "RUA") do nome do logradouro.
    # Precisamos combinar os dois para ter o endereço completo.
    tipo_logradouro = (
        dados.get("descricao_tipo_logradouro", "")
        or dados.get("tipo_logradouro", "")
        or ""
    ).strip()
    nome_logradouro = dados.get("logradouro", "").strip()

    # Ex: "AVENIDA" + "CONSELHEIRO CARRAO" → "AVENIDA CONSELHEIRO CARRAO"
    rua_completa = f"{tipo_logradouro} {nome_logradouro}".strip() if tipo_logradouro else nome_logradouro

    partes_endereco = [
        rua_completa,
        dados.get("numero", ""),
        dados.get("complemento", ""),
        dados.get("bairro", ""),
        dados.get("municipio", ""),
        dados.get("uf", ""),
    ]
    endereco_completo = ", ".join(p for p in partes_endereco if p)

    # Formata o CEP retornado
    cep_raw = re.sub(r'\D', '', dados.get("cep", "") or "")
    cep_formatado = f"{cep_raw[:5]}-{cep_raw[5:]}" if len(cep_raw) == 8 else ""

    return DadosCNPJ(
        razao_social=dados.get("razao_social", ""),
        nome_fantasia=dados.get("nome_fantasia") or None,
        cnpj=cnpj_limpo,
        cep=cep_formatado or None,
        logradouro=endereco_completo or None,
        numero=dados.get("numero") or None,
        complemento=dados.get("complemento") or None,
        municipio=dados.get("municipio") or None,
        uf=dados.get("uf") or None,
        telefone=dados.get("ddd_telefone_1") or None,
        situacao_cadastral=dados.get("descricao_situacao_cadastral") or None,
    )


def _montar_resposta_cep(logradouro: str, bairro: str, municipio: str, uf: str, cep: str) -> dict:
    """Monta o dicionário de resposta padronizado para consultas de CEP."""
    endereco_completo = ", ".join(filter(bool, [logradouro, bairro, municipio, uf]))
    return {
        "cep": cep,
        "logradouro": logradouro,
        "bairro": bairro,
        "municipio": municipio,
        "uf": uf,
        "endereco_completo": endereco_completo,
    }


@router.get(
    "/cep/{cep}",
    summary="Consultar endereço pelo CEP"
)
async def consultar_cep(cep: str):
    """
    Busca o endereço a partir do CEP.

    Estratégia: tenta BrasilAPI CEP v2 primeiro (agrega várias fontes e
    retorna o tipo do logradouro junto, ex: "Avenida Paulista").
    Se falhar, cai no ViaCEP como fallback.

    Exemplo: GET /consulta/cep/01310100
    """
    cep_limpo = re.sub(r'\D', '', cep)

    if len(cep_limpo) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CEP deve ter 8 dígitos"
        )

    cep_formatado = f"{cep_limpo[:5]}-{cep_limpo[5:]}"

    async with httpx.AsyncClient(timeout=8.0) as client:

        # ── 1ª tentativa: BrasilAPI CEP v2 ──────────────────────────────
        try:
            resp = await client.get(f"{BRASIL_API_CEP_URL}/{cep_limpo}")
            if resp.status_code == 200:
                d = resp.json()
                return _montar_resposta_cep(
                    logradouro=d.get("street", ""),
                    bairro=d.get("neighborhood", ""),
                    municipio=d.get("city", ""),
                    uf=d.get("state", ""),
                    cep=cep_formatado,
                )
            if resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CEP não encontrado"
                )
        except httpx.TimeoutException:
            pass   # Segue para o fallback

        # ── 2ª tentativa: ViaCEP (fallback) ─────────────────────────────
        try:
            resp = await client.get(f"{VIACEP_URL}/{cep_limpo}/json/")
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Timeout ao consultar CEP — tente novamente"
            )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Erro ao consultar CEP")

    d = resp.json()
    if d.get("erro"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CEP não encontrado"
        )

    return _montar_resposta_cep(
        logradouro=d.get("logradouro", ""),
        bairro=d.get("bairro", ""),
        municipio=d.get("localidade", ""),
        uf=d.get("uf", ""),
        cep=d.get("cep", cep_formatado),
    )
