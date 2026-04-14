"""
models.py - Modelos do banco de dados (tabelas)

Aqui definimos as tabelas do banco usando classes Python (isso é OOP!).
Cada classe representa uma tabela, e cada atributo da classe representa uma coluna.

INTRODUÇÃO À POO (Programação Orientada a Objetos) neste arquivo:
- Uma CLASSE é como um molde/formulário em branco
- Um OBJETO é um formulário preenchido (um registro na tabela)
- HERANÇA: nossas classes herdam de 'Base' (do SQLAlchemy), ganhando
  os poderes de se tornarem tabelas no banco de dados automaticamente
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum,
    ForeignKey, Date, Time, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


# ============================================================
# ENUMERAÇÕES - São como listas fixas de opções permitidas
# ============================================================

class RoleUsuario(str, enum.Enum):
    """Define os tipos de acesso no sistema"""
    LIDER_MINISTERIO = "LIDER_MINISTERIO"   # Admin master (antigo Pastor Presidente)
    LIDER            = "LIDER"              # Admin de departamento
    MEMBRO           = "MEMBRO"             # Usuário comum


class GeneroUsuario(str, enum.Enum):
    """Gênero do usuário (define os cargos disponíveis)"""
    MASCULINO = "MASCULINO"
    FEMININO  = "FEMININO"


class CargoUsuario(str, enum.Enum):
    """Cargos eclesiásticos"""
    # Homens
    MEMBRO      = "Membro"
    COOPERADOR  = "Cooperador"
    DIACONO     = "Diácono"
    PRESBITERO  = "Presbítero"
    EVANGELISTA = "Evangelista"
    PASTOR      = "Pastor"
    BISPO       = "Bispo"
    APOSTOLO    = "Apóstolo"
    # Mulheres
    MEMBRA      = "Membra"
    COOPERADORA = "Cooperadora"
    DIACONISA   = "Diaconisa"
    MISSIONARIA = "Missionária"
    PASTORA     = "Pastora"


class StatusEscala(str, enum.Enum):
    """Status de uma escala mensal"""
    RASCUNHO   = "RASCUNHO"    # Em montagem, não visível aos membros
    PUBLICADA  = "PUBLICADA"   # Publicada, membros já foram notificados
    ARQUIVADA  = "ARQUIVADA"   # Mês passado, arquivada para histórico


class DiaSemana(str, enum.Enum):
    """Dias da semana para cultos recorrentes"""
    SEGUNDA    = "SEGUNDA"
    TERCA      = "TERCA"
    QUARTA     = "QUARTA"
    QUINTA     = "QUINTA"
    SEXTA      = "SEXTA"
    SABADO     = "SABADO"
    DOMINGO    = "DOMINGO"


class CanalNotificacao(str, enum.Enum):
    """Canais de envio de notificações"""
    APP       = "APP"
    WHATSAPP  = "WHATSAPP"


# ============================================================
# TABELA: igrejas
# ============================================================

class Igreja(Base):
    """
    Representa a Igreja - é o 'guarda-chuva' de tudo no sistema.
    Todos os usuários, departamentos e escalas pertencem a uma Igreja.
    """
    __tablename__ = "igrejas"

    id          = Column(Integer, primary_key=True, index=True)
    nome        = Column(String(200), nullable=False)
    cnpj        = Column(String(18), unique=True, nullable=False)   # "00.000.000/0000-00"
    cep         = Column(String(9), nullable=False)                 # "00000-000"
    logradouro  = Column(String(200), nullable=False)               # "Avenida Paulista"
    numero      = Column(String(20), nullable=True)                 # "1578"
    complemento = Column(String(100), nullable=True)                # "Sala 3"
    bairro      = Column(String(100), nullable=False)
    cidade      = Column(String(100), nullable=False)
    uf          = Column(String(2), nullable=False)                 # "SP"
    telefone    = Column(String(20), nullable=True)
    criado_em   = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos: uma Igreja tem muitos Usuários e Departamentos
    # 'back_populates' cria a relação no sentido inverso também
    usuarios     = relationship("Usuario", back_populates="igreja")
    departamentos = relationship("Departamento", back_populates="igreja")
    dias_culto   = relationship("DiaCulto", back_populates="igreja")


# ============================================================
# TABELA: usuarios
# ============================================================

class Usuario(Base):
    """
    Representa qualquer pessoa no sistema:
    Líder do Ministério, Líder de Departamento ou Membro comum.
    """
    __tablename__ = "usuarios"

    id             = Column(Integer, primary_key=True, index=True)
    igreja_id      = Column(Integer, ForeignKey("igrejas.id"), nullable=False)
    nome           = Column(String(150), nullable=False)
    cpf            = Column(String(14), unique=True, nullable=True)   # "000.000.000-00"
    email          = Column(String(150), unique=True, index=True, nullable=False)
    telefone       = Column(String(20), nullable=True)   # Número do WhatsApp
    senha_hash     = Column(String(255), nullable=False)
    role           = Column(Enum(RoleUsuario), default=RoleUsuario.MEMBRO, nullable=False)
    genero         = Column(Enum(GeneroUsuario), nullable=False)
    cargo          = Column(Enum(CargoUsuario), nullable=False)
    foto_url       = Column(String(300), nullable=True)
    ativo          = Column(Boolean, default=True)
    criado_em      = Column(DateTime, default=datetime.utcnow)
    atualizado_em  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    igreja              = relationship("Igreja", back_populates="usuarios")
    departamentos       = relationship("UsuarioDepartamento", back_populates="usuario")
    entradas_escala     = relationship("EntradaEscala", back_populates="usuario")
    notificacoes        = relationship("Notificacao", back_populates="usuario")


# ============================================================
# TABELA: departamentos
# ============================================================

class Departamento(Base):
    """
    Representa um departamento da Igreja (Obreiros, Mídia, Som, etc.)
    Cada departamento tem suas próprias escalas.
    """
    __tablename__ = "departamentos"

    id          = Column(Integer, primary_key=True, index=True)
    igreja_id   = Column(Integer, ForeignKey("igrejas.id"), nullable=False)
    nome        = Column(String(150), nullable=False)
    descricao   = Column(Text, nullable=True)
    cor         = Column(String(7), default="#3B82F6")  # Cor em hex para o app
    ativo       = Column(Boolean, default=True)
    criado_em   = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    igreja      = relationship("Igreja", back_populates="departamentos")
    membros     = relationship("UsuarioDepartamento", back_populates="departamento")
    escalas     = relationship("Escala", back_populates="departamento")


# ============================================================
# TABELA: usuario_departamentos (tabela de ligação N:N)
# ============================================================

class UsuarioDepartamento(Base):
    """
    Tabela de ligação entre Usuário e Departamento.
    Um usuário pode estar em VÁRIOS departamentos.
    Um departamento tem VÁRIOS usuários.
    Isso se chama relação Muitos-para-Muitos (N:N).

    Exemplo: Fulano pode ser membro de 'Obreiros' E 'Mídia' ao mesmo tempo.
    """
    __tablename__ = "usuario_departamentos"

    id              = Column(Integer, primary_key=True, index=True)
    usuario_id      = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=False)
    is_lider        = Column(Boolean, default=False)  # True = líder do departamento
    criado_em       = Column(DateTime, default=datetime.utcnow)

    # Garante que um usuário não seja adicionado duas vezes ao mesmo departamento
    __table_args__ = (
        UniqueConstraint("usuario_id", "departamento_id", name="uq_usuario_departamento"),
    )

    # Relacionamentos
    usuario      = relationship("Usuario", back_populates="departamentos")
    departamento = relationship("Departamento", back_populates="membros")


# ============================================================
# TABELA: dias_culto
# ============================================================

class DiaCulto(Base):
    """
    Define os dias e horários dos cultos da Igreja.
    Pode ser recorrente (toda terça às 19:30) ou esporádico (data específica).
    """
    __tablename__ = "dias_culto"

    id              = Column(Integer, primary_key=True, index=True)
    igreja_id       = Column(Integer, ForeignKey("igrejas.id"), nullable=False)
    descricao       = Column(String(150), nullable=False)  # Ex: "Culto de Terça"
    recorrente      = Column(Boolean, default=True)

    # Para cultos recorrentes (ex: toda Terça-feira)
    dia_semana      = Column(Enum(DiaSemana), nullable=True)

    # Para cultos esporádicos (ex: Retiro dia 15/06)
    data_especifica = Column(Date, nullable=True)

    horario         = Column(Time, nullable=False)
    ativo           = Column(Boolean, default=True)
    criado_em       = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    igreja          = relationship("Igreja", back_populates="dias_culto")
    entradas_escala = relationship("EntradaEscala", back_populates="dia_culto")


# ============================================================
# TABELA: escalas
# ============================================================

class Escala(Base):
    """
    Representa uma escala mensal de um departamento.
    Exemplo: 'Escala de Obreiros - Maio 2025'.

    Uma escala tem várias EntradaEscala (quem serve em cada dia).
    """
    __tablename__ = "escalas"

    id              = Column(Integer, primary_key=True, index=True)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=False)
    mes             = Column(Integer, nullable=False)   # 1-12
    ano             = Column(Integer, nullable=False)
    status          = Column(Enum(StatusEscala), default=StatusEscala.RASCUNHO)
    prazo_limite    = Column(Date, nullable=True)   # Data limite para montar a escala
    publicada_em    = Column(DateTime, nullable=True)
    criado_por_id   = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em       = Column(DateTime, default=datetime.utcnow)

    # Garante que não haja duas escalas do mesmo departamento no mesmo mês/ano
    __table_args__ = (
        UniqueConstraint("departamento_id", "mes", "ano", name="uq_escala_mes_ano"),
    )

    # Relacionamentos
    departamento = relationship("Departamento", back_populates="escalas")
    entradas     = relationship("EntradaEscala", back_populates="escala", cascade="all, delete-orphan")
    criado_por   = relationship("Usuario", foreign_keys=[criado_por_id])


# ============================================================
# TABELA: entradas_escala
# ============================================================

class EntradaEscala(Base):
    """
    Representa uma entrada específica na escala:
    'Fulano serve no dia 04/05/2025 (Culto de Domingo manhã)'.

    REGRA DE NEGÓCIO PRINCIPAL:
    Um mesmo usuário NÃO pode ter duas EntradaEscala na mesma data.
    Essa restrição é verificada no código e no banco.
    """
    __tablename__ = "entradas_escala"

    id           = Column(Integer, primary_key=True, index=True)
    escala_id    = Column(Integer, ForeignKey("escalas.id"), nullable=False)
    usuario_id   = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    dia_culto_id = Column(Integer, ForeignKey("dias_culto.id"), nullable=False)
    data         = Column(Date, nullable=False)   # Data exata do culto
    observacao   = Column(String(300), nullable=True)
    criado_em    = Column(DateTime, default=datetime.utcnow)

    # Garante: mesma pessoa NÃO pode ter duas escalas no mesmo dia
    __table_args__ = (
        UniqueConstraint("usuario_id", "data", name="uq_usuario_data_escala"),
    )

    # Relacionamentos
    escala    = relationship("Escala", back_populates="entradas")
    usuario   = relationship("Usuario", back_populates="entradas_escala")
    dia_culto = relationship("DiaCulto", back_populates="entradas_escala")


# ============================================================
# TABELA: notificacoes
# ============================================================

class Notificacao(Base):
    """
    Registro de notificações enviadas aos usuários.
    Pode ser via App (push) ou WhatsApp.
    """
    __tablename__ = "notificacoes"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo     = Column(String(200), nullable=False)
    mensagem   = Column(Text, nullable=False)
    canal      = Column(Enum(CanalNotificacao), nullable=False)
    lida       = Column(Boolean, default=False)
    enviada    = Column(Boolean, default=False)
    enviada_em = Column(DateTime, nullable=True)
    criado_em  = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    usuario = relationship("Usuario", back_populates="notificacoes")
