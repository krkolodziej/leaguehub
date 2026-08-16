# LeagueHub

LeagueHub is a portfolio-ready SaaS for managing amateur football leagues. It
will eventually cover organizations, seasons, teams, rosters, fixtures, live
match events, standings, statistics, and notifications.

This repository is being built stage by stage as a learning project. Stage 0
only bootstraps the development environment; it does not contain league domain
models, authentication, or API endpoints yet.

## Stack

- Backend: Python 3.13, Django 6.0, PostgreSQL, Redis
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
uv sync --dev
uv run python manage.py check
uv run python manage.py runserver 0.0.0.0:8000
```

In another terminal:

```bash
cd frontend
pnpm install
pnpm dev --host 0.0.0.0
```

The frontend is available at `http://localhost:5173` and the Django
development server at `http://localhost:8000`. During Stage 0 Django uses its
default SQLite database; PostgreSQL is prepared by Compose and will be wired
into Django in Stage 1.

Stop the infrastructure when finished:

```bash
docker compose down
```

## Verification

Stage 0 checks are documented and run before the stage commit:

```bash
cd backend
uv run ruff check .
uv run python manage.py check
uv run python manage.py test
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
