# CLAUDE.md — Smart Finances Backend

This document is the primary reference for AI assistants working on this codebase. It covers architecture, conventions, testing, and workflows.

---

## Project Overview

**Smart Finances Backend** is a FastAPI-based personal finance management REST API. It manages user accounts, transactions, categories, tags, and provides financial reporting with multi-currency support.

- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.x
- **Database**: SQLite (dev/test) or PostgreSQL (production)
- **Auth**: JWT (HS256) via Supabase
- **Deployment**: Vercel (serverless Python)

---

## Repository Structure

```
smart-finances-back/
├── app/                        # Main application package
│   ├── __init__.py             # FastAPI app factory, router registration, CORS
│   ├── config/
│   │   ├── settings.py         # Pydantic BaseSettings (reads from .env)
│   │   ├── database.py         # SQLAlchemy engine + session factory
│   │   └── db_base.py          # Declarative Base for all ORM models
│   ├── entities/               # SQLAlchemy ORM models (DB tables)
│   ├── repository/             # Data access layer (CRUD, raw DB queries)
│   ├── services/               # Business logic layer
│   ├── engines/                # Complex algorithms (e.g., balance computation)
│   ├── schemas/                # Pydantic models for request/response validation
│   ├── routes/                 # FastAPI endpoint definitions
│   ├── dependencies/           # FastAPI Depends() factories per domain
│   └── shared/helpers/         # Shared utilities (date helpers, etc.)
├── tests/                      # Pytest test suite
│   └── conftest.py             # Shared fixtures (DB, client, auth headers)
├── docs/                       # Architecture & design documentation
├── scripts/                    # Local development shell scripts
├── commands/                   # Utility CLI scripts (token generation, etc.)
├── create_db.py                # One-shot DB table creation script
├── pyproject.toml              # Python project config (Black, isort, mypy, pytest)
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development/test dependencies
└── vercel.json                 # Vercel serverless deployment config
```

---

## Architecture

The codebase follows a strict **layered architecture**. Do not skip layers.

```
Route (FastAPI endpoint)
    │
    ▼
Service (business logic, validation, orchestration)
    │                    │
    ▼                    ▼
Repository           Engine
(SQL/ORM CRUD)   (complex algorithms,
                  e.g., BalanceEngine)
    │
    ▼
Database (SQLAlchemy session)
```

### Layers Explained

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Routes** | `app/routes/` | HTTP request/response only. Delegate all logic to services. |
| **Services** | `app/services/` | Business logic, validation, error handling. Extend `BaseService`. |
| **Repositories** | `app/repository/` | All DB queries. Extend `BaseRepository`. No business logic here. |
| **Engines** | `app/engines/` | Complex multi-step algorithms. Load data once, compute in-memory. |
| **Schemas** | `app/schemas/` | Pydantic models for request bodies and response shapes. |
| **Entities** | `app/entities/` | SQLAlchemy ORM table definitions only. No business logic. |
| **Dependencies** | `app/dependencies/` | FastAPI `Depends()` factories that wire services/repos per request. |

### BaseService Pattern

All services extend `BaseService[EntityType, SchemaType]` which provides:
- `add()`, `get()`, `get_by_user_id()`, `update()`, `delete()` — generic CRUD
- `before_create()`, `before_update()`, `before_delete()` — override hooks for validation
- Automatic error handling: 404, 409, 422, 500 HTTPException

### BaseRepository Pattern

All repositories extend `BaseRepository[EntityType]` which provides:
- `get()`, `get_by_user_id()`, `add()`, `update()`, `delete()` — generic DB operations
- Automatic commit/rollback
- Protected fields (`created_at`, `updated_at`) are never overwritten by updates

### Engine Pattern

Use engines (not services) for:
- Multi-step aggregation algorithms
- Computations requiring batch data loading
- Anything that would cause N+1 queries if done in a loop

`BalanceEngine` is the reference implementation. See `docs/EnginesArchitecture.md`.

---

## Domain Models

### Core Entities

| Entity | Table | Key Fields |
|--------|-------|-----------|
| `User` | `profiles` | UUID PK, email (unique), currency, language |
| `Account` | `accounts` | UUID, user_id FK, type (cash/credit/debit), currency, initial_balance |
| `Transaction` | `transactions` | UUID, account_id, category_id, type (income/expense), amount (NUMERIC), date |
| `Category` | `categories` | UUID, user_id, type (income/expense), icon, color |
| `Concept` | `concepts` | UUID, user_id, name — transaction labels |
| `Tag` | `tags` | UUID, user_id, name, color |
| `TransactionTag` | `transaction_tags` | Junction table: transaction ↔ tag (M:N) |
| `BalanceSnapshot` | `balance_snapshots` | Cached balance per account/date for reporting |

### Enums

```python
# Transaction types
TransactionType.INCOME / .EXPENSE

# Account types
AccountType.CASH / .CREDIT / .DEBIT

# Category types
CategoryType.INCOME / .EXPENSE
```

### ID Convention

All primary keys use `UUID`. Never use sequential integers.

### Amount Convention

Use `NUMERIC` / `Decimal` for all monetary values. Never use `float`.

---

## API Routes

All routes are prefixed with `/api/v1`.

| Resource | Prefix | Notable Endpoints |
|----------|--------|-------------------|
| Users | `/users` | GET, POST, PUT, DELETE (current user) |
| Accounts | `/accounts` | Full CRUD |
| Transactions | `/transactions` | CRUD + `/recent` + `/transfer` |
| Categories | `/categories` | Full CRUD |
| Tags | `/tags` | Full CRUD |
| Concepts | `/concept` | Full CRUD |
| Reporting | `/reporting` | Summary, cashflow, balance history, period comparison |

### Reporting Endpoints

- `GET /reporting/categories-summary` — aggregated spending by category
- `GET /reporting/cashflow-summary` — income/expense/net totals
- `GET /reporting/period-comparison` — current vs previous period
- `GET /reporting/cashflow/history` — historical series
- `GET /reporting/balance` — current total balance
- `GET /reporting/balance/accounts` — per-account balances
- `GET /reporting/balance/history` — balance chart data

---

## Authentication

- JWT tokens (HS256) from Supabase auth
- Bearer token via `Authorization: Bearer <token>` header
- All protected routes use `get_current_user()` dependency
- User ID extracted from JWT `sub` claim
- Users can only access their own data — enforced at service layer via `user_id`

---

## Configuration & Environment

Settings are managed via `app/config/settings.py` (Pydantic `BaseSettings`). Copy `.env.example` to `.env` for local development.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./smart_finances.db` | DB connection string |
| `DEBUG` | `False` | Enables OpenAPI docs and root endpoint |
| `JWT_SECRET_KEY` | `""` | JWT signing secret |
| `SECRET_KEY` | `""` | Fallback secret key |
| `SUPABASE_URL` | `""` | Supabase project URL |
| `SUPABASE_KEY` | `""` | Supabase anon/service key |
| `BACKEND_CORS_ORIGINS` | `[]` | Allowed CORS origins (list) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `11520` | 8 days |

---

## Development Workflow

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Run Locally

```bash
uvicorn app:app --reload
```

OpenAPI docs at `http://localhost:8000/docs` (only when `DEBUG=True`).

### Create Database Tables

```bash
python create_db.py
```

### Generate a Dev JWT Token

```bash
python commands/generate_user_token.py <email> <password>
```

---

## Testing

### Run Tests

```bash
pytest                          # all tests
pytest tests/test_users.py      # single file
pytest -m unit                  # unit tests only
pytest -m integration           # integration tests only
pytest -n auto                  # parallel (pytest-xdist)
pytest --cov=app --cov-report=term-missing  # with coverage
```

### Coverage Requirement

Minimum **70%** coverage enforced in CI.

### Test Architecture

- **Test DB**: SQLite in a temporary directory per worker (not the app DB)
- **Fixtures in `tests/conftest.py`**:
  - `client` — FastAPI `TestClient` (session-scoped)
  - `auth_headers` — valid JWT `Authorization` headers (function-scoped)
  - `user_id` — random UUID (function-scoped)
  - `create_registered_user` — factory fixture to create a user in DB
  - `db_session_factory` — SQLAlchemy session factory for the test DB
- Each test gets a fresh schema (auto-reset via `_reset_database_state`)
- Do not share state across tests

### Test File Naming

```
tests/
├── test_root.py
├── test_users.py
├── test_accounts.py
├── test_transactions.py
├── test_transaction_service.py     # service-layer tests
├── test_transaction_repository.py  # repository-layer tests
├── test_transaction_schemas.py     # schema validation tests
├── test_categories.py
├── test_concepts.py
└── test_reporting.py
```

---

## Code Quality

### Tools and Standards

| Tool | Config | Standard |
|------|--------|----------|
| **Black** | `pyproject.toml` | Line length 88, Python 3.11+ |
| **isort** | `pyproject.toml` | Black-compatible profile |
| **flake8** | `pyproject.toml` | E9, F63, F7, F82 errors only |
| **mypy** | `pyproject.toml` | Relaxed (warnings, not strict) |

### Run All Checks Locally

```bash
bash scripts/run-checks.sh
```

This runs Black, isort, flake8, mypy, then pytest with coverage.

### Quick Linting Check

```bash
bash scripts/check-linting.sh
```

### Format Code

```bash
black app/ tests/
isort app/ tests/
```

---

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| `ci.yml` | Push/PR to main, develop | Lint + test (gating) |
| `test.yml` | Push/PR to main, develop | Tests on Python 3.11 + 3.12 |
| `lint.yml` | Push/PR to main, develop | Linting only |

Coverage reports uploaded to Codecov.

### Deployment

Deployed to Vercel as a Python serverless function. `vercel.json` routes all traffic to `app/__init__.py`.

---

## Key Conventions to Follow

### DO

- Use `UUID` for all primary keys
- Use `Decimal` / `NUMERIC` for all monetary amounts
- Add type hints to every function signature
- Raise `HTTPException` with appropriate status codes from service layer
- Use `before_create()` / `before_update()` hooks for validation logic
- Batch-load data in engines to avoid N+1 queries
- Scope all DB queries by `user_id` — users must not see each other's data
- Write tests for new routes/services; maintain ≥70% coverage
- Run `black` and `isort` before committing
- Use `logging` (Python stdlib) for debug/error output

### DO NOT

- Skip layers (e.g., query DB directly from a route)
- Put business logic in repositories or entities
- Put SQL queries in services (use repositories)
- Use `float` for money
- Use `int` for IDs
- Import from `app.config.settings` inside entity/schema files
- Hardcode user IDs — always extract from JWT via `get_current_user()`
- Add new columns to `BalanceSnapshot` without updating the snapshot service

### Adding a New Domain Resource

Follow this checklist:

1. **Entity** — add `app/entities/<resource>.py` (SQLAlchemy model)
2. **Schema** — add `app/schemas/<resource>_schemas.py` (Pydantic I/O models)
3. **Repository** — add `app/repository/<resource>_repository.py` (extends `BaseRepository`)
4. **Service** — add `app/services/<resource>_service.py` (extends `BaseService`)
5. **Dependencies** — add `app/dependencies/<resource>_dependencies.py`
6. **Route** — add `app/routes/<resource>_route.py` and register in `app/__init__.py`
7. **Tests** — add `tests/test_<resource>.py`
8. **DB** — import the entity in `create_db.py` so tables are created

---

## Useful Reference Files

| File | Purpose |
|------|---------|
| `docs/BackEndProjectArchitecture.md` | Service + Repository pattern deep-dive |
| `docs/DatabaseSchema.md` | ER diagram and table descriptions |
| `docs/EnginesArchitecture.md` | When/how to use Engines |
| `docs/BalanceEngineDiagrams.md` | Balance computation and snapshot logic |
| `docs/TEST_DOCUMENTATION.md` | Test patterns and fixture guide |
| `docs/ProjectScope.md` | Feature inventory and MVP scope |
| `app/services/base_service.py` | BaseService reference implementation |
| `app/repository/base_repository.py` | BaseRepository reference implementation |
| `app/engines/balance_engine.py` | Engine pattern reference implementation |
| `tests/conftest.py` | All shared test fixtures |
