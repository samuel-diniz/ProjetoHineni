"""
schemas.py - Schemas de validação de dados (Pydantic)

Pydantic valida os dados que chegam e saem da API.
Pense nisso como um "formulário inteligente" que:
- Verifica se os campos obrigatórios estão preenchidos
- Verifica se os tipos de dados estão corretos (ex: email válido)
- Formata a resposta que a API devolve

Padrão utilizado:
- *Criar: dados necessários para criar um registro (enviados pelo cliente)
- *Atualizar: dados opcionais para atualizar um registro
- *Resposta: dados que a API retorna (pode omitir campos sensíveis como senha)
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, time, datetime
import re
from app.models import (
    RoleUsuario, GeneroUsuario, CargoUsuario,
    StatusEscala, DiaSemana, CanalNotificacao
)


# ============================================================
# FUNÇÃO DE VALIDAÇÃO DE CNPJ
# ============================================================

def _validar_algoritmo_cnpj(cnpj: str) -> bool:
    """
    Valida o CNPJ pelo algoritmo dos dígitos verificadores.

    O CNPJ tem 14 dígitos. Os 2 últimos são calculados a partir dos 12 primeiros.
    Se os dígitos calculados baterem com os digitados, o CNPJ é válido.
    """
    # Remove qualquer formatação (pontos, barra, traço)
    cnpj = re.sub(r'\D', '', cnpj)

    if len(cnpj) != 14:
        return False

    # CNPJ com todos os dígitos iguais é inválido (ex: 00000000000000)
    if cnpj == cnpj[0] * 14:
        return False

    # Calcula o 1º dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cnpj[12]) != digito1:
        return False

    # Calcula o 2º dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(cnpj[13]) == digito2


def _formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ para o padrão 00.000.000/0000-00"""
    cnpj = re.sub(r'\D', '', cnpj)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def _formatar_cep(cep: str) -> str:
    """Formata CEP para o padrão 00000-000"""
    cep = re.sub(r'\D', '', cep)
    return f"{cep[:5]}-{cep[5:]}"


def _validar_algoritmo_cpf(cpf: str) -> bool:
    """
    Valida o CPF pelos dígitos verificadores.

    O CPF tem 11 dígitos. Os 2 últimos são calculados a partir dos 9 primeiros.
    Mesmo algoritmo usado pela Receita Federal.
    """
    cpf = re.sub(r'\D', '', cpf)

    if len(cpf) != 11:
        return False

    # CPF com todos os dígitos iguais é inválido (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False

    # Calcula o 1º dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    # Calcula o 2º dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(cpf[10]) == digito2


def _formatar_cpf(cpf: str) -> str:
    """Formata CPF para o padrão 000.000.000-00"""
    cpf = re.sub(r'\D', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


# ============================================================
# SCHEMAS DE IGREJA
# ============================================================

class IgrejaCriar(BaseModel):
    """Dados para criar uma nova Igreja (feito pelo Líder do Ministério no cadastro)"""
    nome:        str = Field(..., min_length=3, max_length=200, description="Nome da Igreja")
    cnpj:        str = Field(..., description="CNPJ no formato 00.000.000/0000-00")
    cep:         str = Field(..., description="CEP no formato 00000-000")
    logradouro:  str = Field(..., min_length=2, max_length=200, description="Nome da rua/avenida com tipo")
    numero:      Optional[str] = Field(None, max_length=20, description="Número do endereço")
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento (sala, apto, etc.)")
    bairro:      str = Field(..., min_length=2, max_length=100)
    cidade:      str = Field(..., min_length=2, max_length=100)
    uf:          str = Field(..., min_length=2, max_length=2, description="Sigla do estado (ex: SP)")
    telefone:    Optional[str] = Field(None, max_length=20)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v):
        """Valida formato e algoritmo do CNPJ"""
        apenas_numeros = re.sub(r'\D', '', v)
        if len(apenas_numeros) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos numéricos")
        if not _validar_algoritmo_cnpj(apenas_numeros):
            raise ValueError("CNPJ inválido — verifique os números digitados")
        return _formatar_cnpj(apenas_numeros)   # Salva já formatado

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v):
        """Valida e formata o CEP"""
        apenas_numeros = re.sub(r'\D', '', v)
        if len(apenas_numeros) != 8:
            raise ValueError("CEP deve ter 8 dígitos numéricos")
        return _formatar_cep(apenas_numeros)   # Salva já formatado


class DadosCNPJ(BaseModel):
    """Dados retornados pela consulta de CNPJ (BrasilAPI)"""
    razao_social:   str
    nome_fantasia:  Optional[str] = None
    cnpj:           str
    cep:            Optional[str] = None
    logradouro:     Optional[str] = None
    numero:         Optional[str] = None
    complemento:    Optional[str] = None
    municipio:      Optional[str] = None
    uf:             Optional[str] = None
    telefone:       Optional[str] = None
    situacao_cadastral: Optional[str] = None


class IgrejaResposta(BaseModel):
    """Dados da Igreja retornados pela API"""
    id:          int
    nome:        str
    cnpj:        str
    cep:         str
    logradouro:  str
    numero:      Optional[str]
    complemento: Optional[str]
    bairro:      str
    cidade:      str
    uf:          str
    telefone:    Optional[str]
    criado_em:   datetime

    model_config = {"from_attributes": True}


# ============================================================
# SCHEMAS DE USUÁRIO
# ============================================================

class UsuarioCriar(BaseModel):
    """Dados para cadastrar um novo usuário"""
    nome:       str = Field(..., min_length=2, max_length=150)
    cpf:        Optional[str] = Field(None, description="CPF no formato 000.000.000-00")
    email:      EmailStr
    telefone:   Optional[str] = Field(None, max_length=20, description="Número com DDD para WhatsApp")
    senha:      str = Field(..., min_length=6, description="Mínimo 6 caracteres")
    genero:     GeneroUsuario
    cargo:      CargoUsuario
    role:       RoleUsuario = RoleUsuario.MEMBRO

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v):
        """Valida formato e algoritmo do CPF (quando informado)"""
        if v is None:
            return v
        apenas_numeros = re.sub(r'\D', '', v)
        if len(apenas_numeros) != 11:
            raise ValueError("CPF deve ter 11 dígitos numéricos")
        if not _validar_algoritmo_cpf(apenas_numeros):
            raise ValueError("CPF inválido — dígitos verificadores incorretos")
        return _formatar_cpf(apenas_numeros)

    # Validação extra: cargos femininos só para mulheres e vice-versa
    @field_validator("cargo")
    @classmethod
    def validar_cargo_genero(cls, cargo, info):
        genero = info.data.get("genero")
        cargos_masculinos = {
            "Membro", "Cooperador", "Diácono", "Presbítero",
            "Evangelista", "Pastor", "Bispo", "Apóstolo"
        }
        cargos_femininos = {"Membra", "Cooperadora", "Diaconisa", "Missionária", "Pastora"}

        if genero == GeneroUsuario.MASCULINO and cargo.value in cargos_femininos:
            raise ValueError(f"Cargo '{cargo.value}' não é válido para homens")
        if genero == GeneroUsuario.FEMININO and cargo.value in cargos_masculinos:
            raise ValueError(f"Cargo '{cargo.value}' não é válido para mulheres")
        return cargo


class UsuarioCriarComIgreja(UsuarioCriar):
    """Para o Líder do Ministério: cadastra a si mesmo E a Igreja ao mesmo tempo"""
    igreja: IgrejaCriar


class UsuarioAtualizar(BaseModel):
    """Campos opcionais para atualizar o perfil"""
    nome:     Optional[str] = Field(None, min_length=2, max_length=150)
    telefone: Optional[str] = Field(None, max_length=20)
    cargo:    Optional[CargoUsuario] = None
    foto_url: Optional[str] = None


class UsuarioResposta(BaseModel):
    """Dados do usuário retornados pela API (sem a senha!)"""
    id:        int
    nome:      str
    cpf:       Optional[str]
    email:     str
    telefone:  Optional[str]
    role:      RoleUsuario
    genero:    GeneroUsuario
    cargo:     CargoUsuario
    ativo:     bool
    igreja_id: int
    criado_em: datetime

    model_config = {"from_attributes": True}


class UsuarioRespostaCompleta(UsuarioResposta):
    """Versão completa com os departamentos que o usuário pertence"""
    departamentos: List["DepartamentoSimples"] = []


# ============================================================
# SCHEMAS DE AUTENTICAÇÃO
# ============================================================

class LoginDados(BaseModel):
    """Dados para fazer login"""
    email: EmailStr
    senha: str


class Token(BaseModel):
    """Token JWT retornado após login bem-sucedido"""
    access_token: str
    token_type:   str = "bearer"
    usuario:      UsuarioResposta


class TokenDados(BaseModel):
    """Dados extraídos do token JWT (uso interno)"""
    usuario_id: Optional[int] = None
    email:      Optional[str] = None


# ============================================================
# SCHEMAS DE DEPARTAMENTO
# ============================================================

class DepartamentoCriar(BaseModel):
    nome:      str = Field(..., min_length=2, max_length=150)
    descricao: Optional[str] = None
    cor:       Optional[str] = Field("#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class DepartamentoAtualizar(BaseModel):
    nome:      Optional[str] = Field(None, min_length=2, max_length=150)
    descricao: Optional[str] = None
    cor:       Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    ativo:     Optional[bool] = None


class DepartamentoSimples(BaseModel):
    """Versão resumida do departamento (para não causar loops nos relacionamentos)"""
    id:       int
    nome:     str
    cor:      str
    is_lider: bool = False

    model_config = {"from_attributes": True}


class DepartamentoResposta(BaseModel):
    id:         int
    nome:       str
    descricao:  Optional[str]
    cor:        str
    ativo:      bool
    criado_em:  datetime
    total_membros: int = 0

    model_config = {"from_attributes": True}


class AdicionarMembroDepartamento(BaseModel):
    """Para adicionar um membro a um departamento"""
    usuario_id: int
    is_lider:   bool = False


# ============================================================
# SCHEMAS DE DIA DE CULTO
# ============================================================

class DiaCultoCriar(BaseModel):
    descricao:       str = Field(..., min_length=3, max_length=150)
    recorrente:      bool = True
    dia_semana:      Optional[DiaSemana] = None
    data_especifica: Optional[date] = None
    horario:         time

    @field_validator("dia_semana", "data_especifica")
    @classmethod
    def validar_recorrencia(cls, v, info):
        """Culto recorrente precisa de dia_semana; esporádico precisa de data_especifica"""
        recorrente = info.data.get("recorrente")
        campo = info.field_name

        if recorrente and campo == "dia_semana" and v is None:
            raise ValueError("Cultos recorrentes precisam de dia_semana")
        if not recorrente and campo == "data_especifica" and v is None:
            raise ValueError("Cultos esporádicos precisam de data_especifica")
        return v


class DiaCultoResposta(BaseModel):
    id:              int
    descricao:       str
    recorrente:      bool
    dia_semana:      Optional[DiaSemana]
    data_especifica: Optional[date]
    horario:         time
    ativo:           bool

    model_config = {"from_attributes": True}


# ============================================================
# SCHEMAS DE ESCALA
# ============================================================

class EscalaCriar(BaseModel):
    departamento_id: int
    mes:             int = Field(..., ge=1, le=12)
    ano:             int = Field(..., ge=2024)
    prazo_limite:    Optional[date] = None


class EscalaResposta(BaseModel):
    id:              int
    departamento_id: int
    mes:             int
    ano:             int
    status:          StatusEscala
    prazo_limite:    Optional[date]
    publicada_em:    Optional[datetime]
    criado_em:       datetime
    total_entradas:  int = 0

    model_config = {"from_attributes": True}


# ============================================================
# SCHEMAS DE ENTRADA DE ESCALA
# ============================================================

class EntradaEscalaCriar(BaseModel):
    usuario_id:   int
    dia_culto_id: int
    data:         date
    observacao:   Optional[str] = Field(None, max_length=300)


class EntradaEscalaResposta(BaseModel):
    id:          int
    escala_id:   int
    data:        date
    observacao:  Optional[str]
    usuario:     UsuarioResposta
    dia_culto:   DiaCultoResposta

    model_config = {"from_attributes": True}


class ConflittoEscala(BaseModel):
    """Retornado quando há conflito de escala (mesma pessoa, mesmo dia)"""
    usuario_id:   int
    usuario_nome: str
    data:         date
    departamento_conflito: str
    mensagem:     str


# ============================================================
# SCHEMAS DE NOTIFICAÇÃO
# ============================================================

class NotificacaoResposta(BaseModel):
    id:        int
    titulo:    str
    mensagem:  str
    canal:     CanalNotificacao
    lida:      bool
    enviada:   bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class MarcarLidaRequest(BaseModel):
    notificacao_ids: List[int]


# ============================================================
# Schema de resposta genérica
# ============================================================

class MensagemResposta(BaseModel):
    """Para respostas simples de sucesso ou erro"""
    mensagem: str
    sucesso:  bool = True


# Referência circular: DepartamentoSimples é usado em UsuarioRespostaCompleta
UsuarioRespostaCompleta.model_rebuild()
