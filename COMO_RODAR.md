# Como rodar o Hineni

## Pré-requisitos
- Python 3.11+
- Docker Desktop (para o PostgreSQL)
- Git (recomendado)

---

## 1. Subir o banco de dados (PostgreSQL)

```bash
# Na raiz do projeto (onde está o docker-compose.yml)
docker-compose up -d
```

Acesse o pgAdmin em: http://localhost:5050
- Email: admin@hineni.com
- Senha: admin123
- Servidor: host=db, porta=5432, user=hineni, senha=hineni123

---

## 2. Configurar o Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Copiar e configurar variáveis de ambiente
copy .env.example .env
# Abra o .env e configure, especialmente o SECRET_KEY

# Rodar o backend
uvicorn app.main:app --reload --port 8000
```

API disponível em: http://localhost:8000
Documentação interativa: http://localhost:8000/docs

---

## 3. Configurar o Frontend

```bash
# Em outro terminal
cd frontend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar no navegador
python main.py
```

App disponível em: http://localhost:8550

---

## 4. Primeiro uso

1. Acesse http://localhost:8550
2. Clique em "Primeiro acesso? Cadastre sua Igreja"
3. Preencha os dados da Igreja e do Pastor Presidente
4. Após cadastrar, você será redirecionado ao dashboard
5. Crie os departamentos em: Configurações → Departamentos
6. Cadastre os membros e atribua aos departamentos
7. Comece a montar as escalas!

---

## Estrutura do projeto

```
ProjetoHineni/
├── backend/
│   ├── app/
│   │   ├── main.py           ← Entrada do FastAPI
│   │   ├── database.py       ← Conexão com PostgreSQL
│   │   ├── models.py         ← Tabelas do banco (SQLAlchemy)
│   │   ├── schemas.py        ← Validação de dados (Pydantic)
│   │   ├── security.py       ← JWT + bcrypt
│   │   ├── dependencies.py   ← Autenticação nos endpoints
│   │   ├── routers/          ← Endpoints da API
│   │   │   ├── auth.py
│   │   │   ├── usuarios.py
│   │   │   ├── departamentos.py
│   │   │   ├── dias_culto.py
│   │   │   ├── escalas.py
│   │   │   └── notificacoes.py
│   │   └── services/
│   │       ├── pdf_service.py         ← Geração de PDF
│   │       └── notification_service.py ← WhatsApp + App
│   └── requirements.txt
├── frontend/
│   ├── main.py           ← Entrada do Flet (roteamento)
│   ├── api_client.py     ← Chamadas HTTP ao backend
│   ├── pages/            ← Telas do app
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   └── escalas.py
│   └── components/
│       └── navbar.py     ← Menu lateral
└── docker-compose.yml    ← PostgreSQL + pgAdmin
```

---

## Fases do desenvolvimento

- [x] **Fase 1** - Backend base: banco, auth, API
- [x] **Fase 2** - Frontend básico: login, dashboard, escalas
- [ ] **Fase 3** - Tela de montagem de escala com calendário visual
- [ ] **Fase 4** - Tela de membros e gerenciamento de departamentos
- [ ] **Fase 5** - Lembretes automáticos (APScheduler)
- [ ] **Fase 6** - WhatsApp (Evolution API) configuração
- [ ] **Fase 7** - Deploy (VPS + domínio)
- [ ] **Fase 8** - Build Android/iOS (Flet)
