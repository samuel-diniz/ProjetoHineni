"""
routers/auth.py - Endpoints de autenticação

Rotas disponíveis:
  POST /auth/cadastro-igreja  → Cadastra o Pastor Presidente + a Igreja (primeiro uso)
  POST /auth/cadastro         → Cadastra um novo usuário (membro, líder)
  POST /auth/login            → Faz login e retorna o token JWT
  GET  /auth/eu               → Retorna os dados do usuário logado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.security import hash_senha, verificar_senha, criar_token_acesso
from app.dependencies import obter_usuario_atual

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/cadastro-igreja",
    response_model=schemas.Token,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro inicial: Pastor Presidente + Igreja"
)
def cadastrar_pastor_e_igreja(dados: schemas.UsuarioCriarComIgreja, db: Session = Depends(get_db)):
    """
    Endpoint usado apenas no primeiro cadastro do sistema.
    Cria a Igreja e o Pastor Presidente ao mesmo tempo.
    """
    # Verifica se o e-mail já existe
    usuario_existente = db.query(models.Usuario).filter(
        models.Usuario.email == dados.email
    ).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado"
        )

    # 1. Cria a Igreja
    nova_igreja = models.Igreja(
        nome=dados.igreja.nome,
        endereco=dados.igreja.endereco,
        telefone=dados.igreja.telefone,
    )
    db.add(nova_igreja)
    db.flush()  # Envia ao banco para obter o ID, mas ainda não confirma

    # 2. Cria o Pastor Presidente dentro da Igreja
    novo_usuario = models.Usuario(
        igreja_id=nova_igreja.id,
        nome=dados.nome,
        email=dados.email,
        telefone=dados.telefone,
        senha_hash=hash_senha(dados.senha),
        role=models.RoleUsuario.PASTOR_PRESIDENTE,
        genero=dados.genero,
        cargo=dados.cargo,
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # 3. Cria o token de acesso e retorna
    token = criar_token_acesso(dados={"sub": str(novo_usuario.id)})
    return schemas.Token(access_token=token, usuario=novo_usuario)


@router.post(
    "/cadastro",
    response_model=schemas.UsuarioResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo membro ou líder"
)
def cadastrar_usuario(
    dados: schemas.UsuarioCriar,
    igreja_id: int,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    """
    Cadastra um novo usuário na Igreja.
    Apenas o Pastor Presidente ou um Líder pode cadastrar novos usuários.
    """
    # Apenas Pastor ou Líder podem cadastrar
    if usuario_atual.role == models.RoleUsuario.MEMBRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para cadastrar usuários"
        )

    # Garante que o cadastro é na mesma Igreja do usuário logado
    if usuario_atual.role != models.RoleUsuario.PASTOR_PRESIDENTE:
        igreja_id = usuario_atual.igreja_id

    # Verifica se e-mail já existe
    if db.query(models.Usuario).filter(models.Usuario.email == dados.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado"
        )

    novo_usuario = models.Usuario(
        igreja_id=igreja_id,
        nome=dados.nome,
        email=dados.email,
        telefone=dados.telefone,
        senha_hash=hash_senha(dados.senha),
        role=dados.role,
        genero=dados.genero,
        cargo=dados.cargo,
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Login com e-mail e senha"
)
def login(dados: schemas.LoginDados, db: Session = Depends(get_db)):
    """
    Realiza o login e retorna um token JWT.
    Esse token deve ser enviado em todas as requisições seguintes.
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == dados.email,
        models.Usuario.ativo == True
    ).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_token_acesso(dados={"sub": str(usuario.id)})
    return schemas.Token(access_token=token, usuario=usuario)


@router.get(
    "/eu",
    response_model=schemas.UsuarioResposta,
    summary="Dados do usuário logado"
)
def meus_dados(usuario_atual: models.Usuario = Depends(obter_usuario_atual)):
    """Retorna os dados do usuário que está logado"""
    return usuario_atual


@router.post(
    "/alterar-senha",
    response_model=schemas.MensagemResposta,
    summary="Alterar minha senha"
)
def alterar_senha(
    senha_atual: str,
    nova_senha: str,
    db: Session = Depends(get_db),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    """Permite que o usuário troque a própria senha"""
    if not verificar_senha(senha_atual, usuario_atual.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    if len(nova_senha) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ter no mínimo 6 caracteres"
        )

    usuario_atual.senha_hash = hash_senha(nova_senha)
    db.commit()
    return schemas.MensagemResposta(mensagem="Senha alterada com sucesso!")
