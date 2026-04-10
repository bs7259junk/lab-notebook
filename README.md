# Lab Notebook — Electronic Lab Notebook (ELN)

A 21 CFR Part 11 compliant Electronic Lab Notebook built with React, FastAPI, PostgreSQL 16, and Docker. Designed for life-science research teams managing CAR-T cell development, biomarker discovery, and bioprocess optimization workflows.

---

## Quick Start

```bash
bash setup.sh
```

That's it. The script handles everything from first-time setup to a running system.

### What `bash setup.sh` does

1. Checks that Docker and Docker Compose (v2) are installed
2. Creates `.env` from `.env.example` if it doesn't already exist
3. Creates `uploads/` and `logs/` directories if missing
4. Writes three demo data files into `uploads/` (bioreactor log, chromatography trace, PBMC counts)
5. Runs `docker compose up --build -d` to build and start all three containers
6. Polls `docker compose ps` every 2 seconds (up to 120 s) until all containers are running
7. Prints the URLs and demo credentials

---

## Local URLs

| Service     | URL                          |
|-------------|------------------------------|
| Frontend    | http://localhost:3000        |
| Backend API | http://localhost:8003        |
| API Docs    | http://localhost:8003/docs   |
| ReDoc       | http://localhost:8003/redoc  |

---

## Demo Users

All demo users share the password **`Lab2026!`**

| Username | Full Name           | Role(s)                          |
|----------|---------------------|----------------------------------|
| admin    | Lab Administrator   | Administrator                    |
| alice    | Alice Chen          | Scientist                        |
| bob      | Bob Martinez        | Technician                       |
| carol    | Carol Wu            | Research Associate / Scientist   |
| dave     | Dave Kim            | Reviewer                         |

---

## Experiment Data

The seed script loads 10 experiments across 3 projects:

| ID            | Title (abbreviated)                             | Status       | Project          |
|---------------|-------------------------------------------------|--------------|------------------|
| EXP-2026-001  | PBMC Isolation from Healthy Donor Buffy Coats   | draft        | CAR-T Dev        |
| EXP-2026-002  | Lentiviral Transduction of T Cells              | in_progress  | CAR-T Dev        |
| EXP-2026-003  | Serum Protein Profiling by LC-MS/MS             | completed    | Biomarker        |
| EXP-2026-004  | pH and DO Optimization for mAb Production       | under_review | Process Opt      |
| EXP-2026-005  | CAR-T Cytotoxicity Assay — 4-Hour 51Cr Release  | completed    | CAR-T Dev        |
| EXP-2026-006  | T Cell Expansion in G-Rex 10 Bioreactor         | active       | CAR-T Dev        |
| EXP-2026-007  | ELISA Validation of LGALS3BP as CRC Biomarker   | approved     | Biomarker        |
| EXP-2026-008  | Western Blot Confirmation of Top 5 Biomarkers   | in_progress  | Biomarker        |
| EXP-2026-009  | Fed-Batch vs Perfusion Mode Comparison          | completed    | Process Opt      |
| EXP-2026-010  | Protein A Affinity Chromatography Optimization  | draft        | Process Opt      |

The seed also loads 8 catalog materials, 3 projects, lab entries, comments, reviews, and e-signatures.

---

## Common Operations

**Stop all containers:**
```bash
docker compose down
```

**Full reset (wipes database volume and re-seeds):**
```bash
docker compose down -v && bash setup.sh
```

**Tail live logs:**
```bash
docker compose logs -f
```

**Open a database shell:**
```bash
docker exec -it eln_db psql -U elnuser -d elndb
```

**Open a backend shell:**
```bash
docker exec -it eln_backend bash
```

Or use the Makefile shortcuts:

```bash
make up           # same as bash setup.sh
make down         # docker compose down
make reset        # wipe db and re-run setup
make logs         # follow logs
make shell-backend
make shell-db
```

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|-------------------------------------------------|
| Frontend    | React 18, Vite, TypeScript, Nginx               |
| Backend     | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic   |
| Database    | PostgreSQL 16                                   |
| Auth        | python-jose (JWT), passlib[bcrypt]              |
| Validation  | Pydantic v2, pydantic-settings                  |
| DB Driver   | psycopg (v3, binary)                            |
| Container   | Docker Compose v2                               |

---

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
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh            # Runs migrations, auto-seeds, starts uvicorn
├── frontend/                    # React + Vite SPA
├── uploads/                     # File upload storage (mounted into container)
├── logs/                        # Log files
├── docker-compose.yml
├── .env.example                 # Template — copy to .env for overrides
├── Makefile
├── setup.sh                     # One-command startup
└── docs/cfr_part11_notes.md     # 21 CFR Part 11 compliance notes
```

---

## API Endpoints

| Method     | Path                                        | Description                          |
|------------|---------------------------------------------|--------------------------------------|
| POST       | /auth/login                                 | Login, returns JWT tokens            |
| POST       | /auth/refresh                               | Refresh access token                 |
| GET        | /auth/me                                    | Current user info                    |
| GET/POST   | /users                                      | List/create users (admin)            |
| GET/PATCH  | /users/{id}                                 | Get/update user                      |
| POST/DELETE| /users/{id}/roles                           | Assign/remove role                   |
| GET/POST   | /projects                                   | List/create projects                 |
| GET/PATCH  | /projects/{id}                              | Get/update project                   |
| GET/POST   | /experiments                                | List/create experiments              |
| GET/PATCH  | /experiments/{id}                           | Get/update experiment                |
| POST       | /experiments/{id}/status                    | Status transition                    |
| GET/PUT    | /experiments/{id}/entries/{section}         | Upsert lab entry section             |
| GET/POST   | /experiments/{id}/materials                 | List/add material usage              |
| GET/POST   | /experiments/{id}/attachments               | List/upload attachments              |
| GET        | /attachments/{id}/download                  | Download attachment                  |
| GET/POST   | /experiments/{id}/comments                  | List/add comments                    |
| GET/POST   | /experiments/{id}/reviews                   | List/create review                   |
| PATCH      | /reviews/{id}                               | Complete review                      |
| POST       | /experiments/{id}/sign                      | Add e-signature                      |
| GET        | /experiments/{id}/signatures                | List signatures                      |
| GET        | /barcodes/lookup?barcode=                   | Barcode lookup                       |
| GET        | /audit                                      | Paginated audit log (admin/reviewer) |
| GET        | /health                                     | Health check                         |

---

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed for your environment.

| Variable                    | Default                                        | Description                        |
|-----------------------------|------------------------------------------------|------------------------------------|
| DATABASE_URL                | postgresql+psycopg://elnuser:elnpass@db:5432/elndb | PostgreSQL connection string    |
| SECRET_KEY                  | (change in production)                         | JWT signing key                    |
| UPLOAD_DIR                  | /uploads                                       | File upload mount path             |
| CORS_ORIGINS                | ["http://localhost:3000","http://localhost:5173"] | Allowed CORS origins             |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60                                             | JWT access token lifetime          |
| REFRESH_TOKEN_EXPIRE_DAYS   | 7                                              | JWT refresh token lifetime         |

---

## 21 CFR Part 11 Compliance Notes

This system implements the following Part 11 controls:

- **Immutable audit trail** — append-only `audit_logs` table with server-side timestamps; records cannot be modified after creation
- **Unique user identification** — UUID primary keys, unique username and email constraints enforced at DB level
- **Role-based access control** — roles: `admin`, `scientist`, `technician`, `research_associate`, `reviewer`; enforced in service layer
- **Electronic signatures with meaning** — `Signature` records capture type (`completion`, `review`), legally meaningful statement, IP address, and user-agent string
- **Reviewer independence** — service layer enforces that the reviewer of a record cannot be its author
- **Write-locked approved records** — experiments in `approved` or `archived` status cannot be modified
- **Traceable status transitions** — every status change is written to the audit log with actor, timestamp, old value, and new value

See `docs/cfr_part11_notes.md` for a full compliance assessment against each Part 11 subpart.
