# LeagueHub

LeagueHub is a portfolio-ready SaaS for managing amateur football leagues. It
will eventually cover organizations, seasons, teams, rosters, fixtures, live
match events, standings, statistics, and notifications.

This repository is being built stage by stage as a learning project. Stage 1
contains the backend foundation and a health endpoint; league domain models
and authentication will be introduced in later stages.

## Stack

- Backend: Python 3.13, Django 6.0, Django REST Framework, PostgreSQL, Redis
- Frontend: React, TypeScript, Vite, pnpm
- Tooling: uv, Ruff, Docker Compose

## Prerequisites

The primary development environment is Ubuntu 24.04 in WSL with Docker Engine
and Docker Compose available. Install `uv`, Node.js 24+, and pnpm before
following the commands below.

## Local setup

From the repository root in WSL:

```bash
cp .env.example .env

docker compose up -d --wait
```

If port `6379` is already used by another local Redis instance, choose a
different host port without changing the committed Compose defaults:

```bash
REDIS_HOST_PORT=6380 docker compose up -d --wait
```

```bash
cd backend
set -a
source ../.env
set +a
uv sync --dev
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

In another terminal:

```bash
cd frontend
pnpm install
pnpm dev --host 0.0.0.0
```

The frontend is available at `http://localhost:5173` and the Django
development server at `http://localhost:8000`. The Stage 1 API is available at
`/api/v1/health/`, with interactive OpenAPI docs at `/api/docs/` and the raw
schema at `/api/schema/`.

Development settings use PostgreSQL from Compose. Pytest uses an isolated
in-memory SQLite database so unit tests do not depend on a running service.

Stop the infrastructure when finished:

```bash
docker compose down
```

## Verification

Stage checks are documented and run before each stage commit:

```bash
cd backend
uv run ruff check .
uv run python manage.py check
uv run pytest
uv run python manage.py makemigrations --check --dry-run

cd ../frontend
pnpm lint
pnpm build
```

## Repository layout

```text
leaguehub/
├── backend/
├── frontend/
├── docs/
├── compose.yml
├── .env.example
└── README.md
```
