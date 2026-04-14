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
from app.models import (
    RoleUsuario, GeneroUsuario, CargoUsuario,
    StatusEscala, DiaSemana, CanalNotificacao
)


# ============================================================
# SCHEMAS DE IGREJA
# ============================================================

class IgrejaCriar(BaseModel):
    """Dados para criar uma nova Igreja (feito pelo Pastor Presidente no cadastro)"""
    nome:     str = Field(..., min_length=3, max_length=200, description="Nome da Igreja")
    endereco: Optional[str] = Field(None, max_length=300)
    telefone: Optional[str] = Field(None, max_length=20)


class IgrejaResposta(BaseModel):
    """Dados da Igreja retornados pela API"""
    id:        int
    nome:      str
    endereco:  Optional[str]
    telefone:  Optional[str]
    criado_em: datetime

    # Isso diz ao Pydantic para ler atributos de objetos SQLAlchemy
    model_config = {"from_attributes": True}


# ============================================================
# SCHEMAS DE USUÁRIO
# ============================================================

class UsuarioCriar(BaseModel):
    """Dados para cadastrar um novo usuário"""
    nome:       str = Field(..., min_length=2, max_length=150)
    email:      EmailStr
    telefone:   Optional[str] = Field(None, max_length=20, description="Número com DDD para WhatsApp")
    senha:      str = Field(..., min_length=6, description="Mínimo 6 caracteres")
    genero:     GeneroUsuario
    cargo:      CargoUsuario
    role:       RoleUsuario = RoleUsuario.MEMBRO

    # Validação extra: cargos femininos só para mulheres e vice-versa
    @field_validator("cargo")
    @classmethod
    def validar_cargo_genero(cls, cargo, info):
        genero = info.data.get("genero")
        cargos_masculinos = {"Membro", "Cooperador", "Diácono", "Presbítero", "Evangelista", "Pastor"}
        cargos_femininos  = {"Membra", "Cooperadora", "Diaconisa", "Missionária", "Pastora"}

        if genero == GeneroUsuario.MASCULINO and cargo.value in cargos_femininos:
            raise ValueError(f"Cargo '{cargo.value}' não é válido para homens")
        if genero == GeneroUsuario.FEMININO and cargo.value in cargos_masculinos:
            raise ValueError(f"Cargo '{cargo.value}' não é válido para mulheres")
        return cargo


class UsuarioCriarComIgreja(UsuarioCriar):
    """Para o Pastor Presidente: cadastra a si mesmo E a Igreja ao mesmo tempo"""
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
