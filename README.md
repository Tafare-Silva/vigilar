# Vigilar — Sistema de Gestão para Empresa de Segurança

## Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Banco**: PostgreSQL
- **Cache / Broker**: Redis
- **Tarefas assíncronas**: Celery + Celery Beat
- **Frontend**: Django Templates + Tailwind CSS + HTMX + Alpine.js
- **Autenticação**: django-allauth (e-mail + senha)
- **Segurança**: django-axes (brute-force), Argon2 (hash de senhas)

## Estrutura de Apps

| App | Responsabilidade |
|---|---|
| `core` | Usuário customizado, BaseModel, logs de auditoria |
| `clientes` | Cadastro de clientes (PF e PJ) |
| `fornecedores` | Cadastro de fornecedores |
| `servicos` | Catálogo de planos/serviços |
| `contratos` | Contrato liga cliente + serviço, dispara mensalidades |
| `mensalidades` | Parcelas mensais, controle de pagamentos |
| `boletos` | Emissão de boletos via API bancária |
| `rondas` | Registro de rondas e agentes |
| `dashboard` | KPIs e estatísticas |

## Configuração inicial

```bash
# 1. Clone e crie o virtualenv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Instale as dependências
make install

# 3. Configure o ambiente
cp .env.example .env
# edite o .env com suas credenciais

# 4. Banco de dados
createdb vigilar_db
make migrate

# 5. Superusuário
make superuser

# 6. Rode o servidor
make run
```

## Tarefas agendadas (Celery)

```bash
# Em terminais separados:
make celery        # worker
make celery-beat   # agendador
```

## Testes

```bash
make test
```
