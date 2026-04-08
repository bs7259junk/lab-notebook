# Lab Notebook — Electronic Lab Notebook (ELN)

A 21 CFR Part 11 compliant Electronic Lab Notebook backend built with FastAPI, SQLAlchemy 2.x, PostgreSQL 16, and Docker.

## Quick Start

```bash
# Start the database and backend
docker compose up --build

# Run migrations and seed data (first time only, after containers are up)
docker exec eln_backend python -m app.etl.seed

# API docs available at:
# http://localhost:8003/docs   (Swagger UI)
# http://localhost:8003/redoc  (ReDoc)
```

## Default Credentials (seed data)

All seeded users have password: `LabNotebook2026!`

| Username | Email | Roles |
|---|---|---|
| admin | admin@lab.com | admin |
| alice | alice@lab.com | scientist |
| bob | bob@lab.com | technician |
| carol | carol@lab.com | research_associate, scientist |
| dave | dave@lab.com | reviewer |

## Stack

- **Python 3.12** + **FastAPI** — API framework
- **SQLAlchemy 2.x** — ORM with `Mapped`/`mapped_column` typed models
- **Alembic** — database migrations
- **Pydantic v2** + **pydantic-settings** — schema validation and config
- **psycopg (v3)** — PostgreSQL driver
- **PostgreSQL 16** — database
- **python-jose + passlib[bcrypt]** — JWT auth and password hashing
- **Docker Compose** — local development environment

## Directory Structure

```
lab-notebook/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, router registration
│   │   ├── config.py            # pydantic-settings config
│   │   ├── db.py                # SQLAlchemy engine + session
│   │   ├── auth/                # JWT, password hashing, FastAPI dependencies
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── api/                 # FastAPI routers (one file per resource)
│   │   ├── services/            # Business logic layer
│   │   ├── repositories/        # Data access layer
│   │   ├── storage/             # File storage abstraction (local + S3-ready)
│   │   └── etl/seed.py          # Database seed script
│   ├── alembic/                 # Migrations
│   │   └── versions/001_initial.py
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/                    # Placeholder (see frontend/README.md)
├── uploads/                     # File upload storage (mounted into container)
├── logs/                        # Log files
├── docker-compose.yml
├── .env.example
└── docs/cfr_part11_notes.md     # 21 CFR Part 11 compliance notes
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /auth/login | Login, returns JWT tokens |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Current user info |
| GET/POST | /users | List/create users (admin) |
| GET/PATCH | /users/{id} | Get/update user |
| POST/DELETE | /users/{id}/roles | Assign/remove role |
| GET/POST | /projects | List/create projects |
| GET/PATCH | /projects/{id} | Get/update project |
| GET/POST | /experiments | List/create experiments |
| GET/PATCH | /experiments/{id} | Get/update experiment |
| POST | /experiments/{id}/status | Status transition |
| GET/PUT | /experiments/{id}/entries/{section} | Upsert lab entry section |
| GET/POST | /experiments/{id}/materials | List/add material usage |
| GET/POST | /experiments/{id}/attachments | List/upload attachments |
| GET | /attachments/{id}/download | Download attachment |
| GET/POST | /experiments/{id}/comments | List/add comments |
| GET/POST | /experiments/{id}/reviews | List/create review |
| PATCH | /reviews/{id} | Complete review |
| POST | /experiments/{id}/sign | Add e-signature |
| GET | /experiments/{id}/signatures | List signatures |
| GET | /barcodes/lookup?barcode= | Barcode lookup |
| GET | /audit | Paginated audit log (admin/reviewer) |
| GET | /health | Health check |

## 21 CFR Part 11 Features

- **Immutable audit trail** — append-only `audit_logs` table with server-side timestamps
- **Unique user IDs** — UUID PKs, unique username + email constraints
- **Role-based access control** — admin, scientist, technician, research_associate, reviewer
- **Electronic signatures with meaning** — `Signature` records capture type, meaning, IP, user-agent
- **Reviewer ≠ author** — enforced at service layer for review signatures
- **Write-locked approved records** — approved/archived experiments cannot be modified

See `docs/cfr_part11_notes.md` for a full compliance assessment.

## Development

```bash
# Install dependencies locally (for IDE support)
cd backend
pip install -r requirements.txt

# Run migrations manually
alembic upgrade head

# Run seed data
python -m app.etl.seed

# Run tests
pytest
```

## Environment Variables

See `.env.example` for all configuration options. Copy to `.env` for local overrides.

Key variables:
- `DATABASE_URL` — PostgreSQL connection string (auto-normalizes `postgresql://` → `postgresql+psycopg://`)
- `SECRET_KEY` — JWT signing key (change in production!)
- `UPLOAD_DIR` — Directory for file uploads
- `CORS_ORIGINS` — JSON array of allowed CORS origins
