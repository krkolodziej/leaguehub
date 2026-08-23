# LeagueHub

LeagueHub is a portfolio-ready SaaS for managing amateur football leagues. It
will eventually cover organizations, seasons, teams, rosters, fixtures, live
match events, standings, statistics, and notifications.

This repository is being built stage by stage as a learning project. It now
contains the backend foundation, Django session authentication, multi-tenant
organizations/RBAC, the league competition domain, deterministic round-robin
fixture generation, match lifecycle events, and derived standings/statistics.

## Stack

- Backend: Python 3.13, Django 6.0, Django REST Framework, PostgreSQL, Redis,
  django-cors-headers
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
development server at `http://localhost:8000`. The API health check is
available at `/api/v1/health/`. Session authentication uses
`/api/v1/auth/csrf/`, `/api/v1/auth/register/`, `/api/v1/auth/login/`,
`/api/v1/auth/logout/`, and `/api/v1/auth/me/`. Interactive OpenAPI docs are
at `/api/docs/` and the raw schema is at `/api/schema/`.

Organization management uses `/api/v1/organizations/` and nested `members/`
endpoints. Each organization has `OWNER`, `ADMIN`, and `MEMBER` roles. The
backend scopes organization QuerySets by the authenticated user's membership;
frontend checks are never treated as a security boundary.

The competition domain contains `League`, `Season`, `Team`, `SeasonTeam`,
`Player`, and `RosterEntry`. A team is attached to a season through
`SeasonTeam`, while a player is attached to a seasonal team through
`RosterEntry`. Competition API routes are nested under an organization and
enforce the same backend membership and manager permissions.

Fixture generation is available at the season-level `fixtures/` endpoint. A
single round robin creates one pairing for every team pair; a double round
robin adds the reversed home/away pairing. Generation is deterministic,
transactional, and rejects a second request for the same season.

Stage 6 adds the match lifecycle and match events. A fixture can have one
`Match`, whose state moves through explicit transitions such as `SCHEDULED`,
`LIVE`, `FINISHED`, `CANCELLED`, and `POSTPONED`. Events are accepted only for
live matches, and a goal updates the corresponding home or away score in the
same database transaction as the event. Players must be rostered for the
fixture's season and team. Match and event routes are nested under the same
organization/league/season scope and manager writes are enforced server-side.

Stage 7 adds derived season standings at `standings/` using only `FINISHED`
matches and the 3/1/0 scoring system. Rows are ordered by points, goal
difference, goals for, team name, and team ID. Player statistics and the top
scorers list are available under `statistics/players/` and
`statistics/top-scorers/`; they aggregate finished-match goals and cards from
`MatchEvent`. Appearances are intentionally not reported yet because the
domain does not store lineups or minutes played. Aggregation queries use
related filters and dedicated indexes to avoid N+1 event lookups.

For a browser client, request `/api/v1/auth/csrf/` first, then send the
`csrftoken` cookie value in the `X-CSRFToken` header for register, login, and
logout. Cross-origin requests must include credentials; local origins are
configured through `DJANGO_CORS_ALLOWED_ORIGINS`.

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
