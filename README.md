# LeagueHub

LeagueHub runs an amateur football league. It holds the clubs, squads and
season calendar, records what happens in each match, and derives the league
table and player statistics from those records rather than from figures anyone
types in by hand.

One organization can run several leagues; each league runs seasons; each season
has its clubs, their squads, a generated fixture list and the matches played
against it. Everything a reader sees — the table, the top scorers, a club's
recent form — is computed from match events.

## What it does

**Competition structure.** Organizations own leagues, leagues own seasons, and
a season registers clubs through `SeasonTeam` and squads through `RosterEntry`.
Three roles govern access: `OWNER`, `ADMIN` and `MEMBER`. Every queryset is
scoped by the requesting user's membership on the server; the UI's own checks
are never the security boundary.

**Fixtures.** A season generates its whole calendar in one deterministic,
transactional step — single or double round robin, one pairing per club pair,
home and away reversed for the second leg. A season refuses to generate twice.

**Matches.** Each fixture carries one match moving through `SCHEDULED`, `LIVE`,
`FINISHED`, `CANCELLED` and `POSTPONED` by explicit transitions. Goals and cards
are accepted only while a match is live, only for players rostered to that club
for that season, and a goal updates the score in the same transaction that
records the event. A score therefore cannot disagree with its events.

**Standings and statistics.** The table counts finished matches only, on 3/1/0,
ordered by points, goal difference, goals for, then club name. Top scorers and
disciplinary records aggregate the same match events.

**Live matches.** A match in progress pushes goals and cards to anyone watching
over an authenticated WebSocket. Broadcasts are scheduled after the database
transaction commits, so a rolled-back change is never sent.

**Notifications.** Finishing a match notifies the organization's managers, and
a periodic scan raises reminders for upcoming kick-offs. Dedupe keys make
delivery idempotent.

**The interface.** A React SPA covering sign-in, the organization dashboard,
league management forms, and per-league views for fixtures, the table, clubs,
statistics and match detail. The design follows [docs/DESIGN.md](docs/DESIGN.md):
a printed-league-table treatment with tabular figures, club crests derived from
club names, a form guide, and yellow and red reserved strictly for cards.

## Stack

- **Backend** — Python 3.13, Django 6.0, Django REST Framework, Channels,
  Celery, PostgreSQL, Redis
- **Frontend** — React 19, TypeScript, Vite, TanStack Query, React Router,
  Tailwind CSS, shadcn/ui
- **Tooling** — uv, Ruff, pytest, Vitest, Playwright, oxlint, Docker

## Running it locally

The development environment is Ubuntu 24.04 under WSL with Docker. Install
`uv`, Node.js 24+ and pnpm first.

```bash
cp .env.example .env
docker compose up -d --wait
```

If port `6379` is taken by another Redis, pick a different host port without
editing the committed defaults:

```bash
REDIS_HOST_PORT=6380 docker compose up -d --wait
```

Then the backend:

```bash
cd backend
set -a; source ../.env; set +a
uv sync --dev
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver 0.0.0.0:8000
```

And the frontend, in another terminal:

```bash
cd frontend
pnpm install
pnpm dev --host 0.0.0.0
```

The app is at `http://localhost:5173`, the API at `http://localhost:8000`.
Vite proxies `/api` and `/ws` to Django, so both share an origin in the
browser and session cookies work without any CORS configuration.

> Vite's file watcher does not see edits made on a Windows drive from inside
> WSL. If a change does not appear, restart `pnpm dev`.

Background processes, when you want reminders and post-match notifications:

```bash
uv run celery -A config worker --loglevel=INFO
uv run celery -A config beat --loglevel=INFO
```

## Signing in

`seed_demo` populates a full season and creates three accounts, one per role,
all with the password `demo1234`:

| Email | Role |
| --- | --- |
| `demo@leaguehub.app` | Owner |
| `admin@leaguehub.app` | Admin |
| `member@leaguehub.app` | Member |

The sign-in screen offers the owner account behind a single button. The
frontend reads it from `VITE_DEMO_EMAIL` and `VITE_DEMO_PASSWORD`; build with
an empty `VITE_DEMO_EMAIL` to remove that block.

## Seeded data

`python manage.py seed_demo` builds one organization, a league and season,
twelve clubs with full squads, a complete double round robin of 132 fixtures,
and results for roughly the first 60 per cent of the calendar. Scores come from
seeded match events, so standings and player statistics are derived from the
same data an operator would enter by hand. One match is left in progress and a
few are cancelled or postponed, so every state is visible.

Results are drawn against hidden club strengths with a home advantage, which
gives the table a credible spread instead of uniform noise. The command is
deterministic, runs inside one transaction, and is idempotent — running it
again leaves the existing dataset alone. Pass `--flush` to discard the seeded
records and rebuild them:

```bash
python manage.py seed_demo --flush
```

## API

Interactive OpenAPI docs are at `/api/docs/`, the raw schema at `/api/schema/`,
and a health check at `/api/v1/health/`.

Authentication is session-based: `/api/v1/auth/csrf/`, `register/`, `login/`,
`logout/` and `me/`. A browser client requests the CSRF cookie first, then
echoes it in `X-CSRFToken` on every mutating request.

Competition routes nest under an organization, for example
`/api/v1/organizations/{id}/leagues/{id}/seasons/{id}/` followed by `teams/`,
`fixtures/`, `matches/`, `standings/`, `statistics/players/` or
`statistics/top-scorers/`. Collections accept optional `page` and `page_size`
and return `count`, `next`, `previous` and `results`; without them the plain
list is returned. Errors share one shape: `detail`, `code`, and `fields` for
validation failures.

## Architecture and domain model

```mermaid
flowchart LR
  Browser --> Web["gunicorn, uvicorn worker"]
  Web --> Static["WhiteNoise: compiled SPA and static files"]
  Web --> API["Django REST and Channels"]
  API --> PostgreSQL[(PostgreSQL)]
  API -. only when REDIS_URL is set .-> Redis[(Redis)]
  Redis -.-> Celery["Celery worker and beat"]
```

Without `REDIS_URL` a single instance fans live updates out in-process and runs
notification tasks inline. `compose.production.yml` runs the alternative shape:
Nginx in front, Daphne serving Django, and Redis, the Celery worker and beat as
their own services.

```mermaid
erDiagram
  ORGANIZATION ||--o{ LEAGUE : owns
  LEAGUE ||--o{ SEASON : contains
  SEASON ||--o{ SEASON_TEAM : includes
  TEAM ||--o{ SEASON_TEAM : appears
  SEASON_TEAM ||--o{ ROSTER_ENTRY : has
  PLAYER ||--o{ ROSTER_ENTRY : assigned
  SEASON ||--o{ FIXTURE : schedules
  FIXTURE ||--|| MATCH : records
  MATCH ||--o{ MATCH_EVENT : contains
```

See [architecture](docs/architecture.md), [domain model](docs/domain-model.md),
[trade-offs](docs/tradeoffs.md), [design](docs/DESIGN.md) and
[interview notes](docs/interview-notes.md) for the detailed design and its
constraints. The stage-by-stage record of how the application was built lives
in the [development log](docs/CHANGELOG.md).

## Deploying

One service builds the root [`Dockerfile`](Dockerfile), which compiles the SPA
and then serves it and the API from the same origin under gunicorn with a
uvicorn worker class. Static files go through WhiteNoise; the ASGI worker keeps
the live-match WebSocket working. The image is plain Docker and takes its
database from `DATABASE_URL`, so it runs unchanged on any container host.

Serving both halves from one origin is deliberate. Split across two subdomains
of a platform's shared domain they would be cross-site, because those suffixes
are on the Public Suffix List, and the `SameSite=Lax` session cookie would never
be sent with an API call.

Two configurations are checked in: [`render.yaml`](render.yaml) for a free
deployment and [`railway.json`](railway.json) for Railway. Neither needs the
hostname up front — production settings read `RENDER_EXTERNAL_HOSTNAME` or
`RAILWAY_PUBLIC_DOMAIN` and add it to `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS` themselves.

## Deploying free: Render and Neon

Render runs the container, Neon holds the database. Both have a permanent free
plan and neither asks for a card.

The database is on Neon rather than Render on purpose: **a free Render Postgres
is deleted 30 days after it is created**, while a free Neon project is
permanent.

1. Create a Postgres project at [neon.com](https://neon.com) and copy the
   pooled connection string (it ends in `?sslmode=require`).
2. At [render.com](https://render.com), choose **New → Blueprint** and point it
   at this repository. Render reads `render.yaml` and asks for one value:
   paste the Neon string into `DATABASE_URL`.
3. Deploy. The container applies migrations and seeds the league on start, so
   the first page load already has a full season behind it.

What free costs you:

- The service **sleeps after 15 minutes** without traffic and takes about a
  minute to wake, so the first visit after a quiet spell is slow.
- 750 instance hours per workspace per month.
- Neon suspends idle compute too, adding a second or two to the first query.
- Live match updates are fanned out in-process, because there is no Redis. That
  is why `WEB_CONCURRENCY` is `1`; a second worker would not see them.

Pre-deploy commands are a paid Render feature, so `RUN_RELEASE_ON_START=true`
makes [`backend/docker-entrypoint.sh`](backend/docker-entrypoint.sh) run
`migrate` and `seed_demo` before gunicorn starts. Both are safe to repeat, which
matters because every wake from sleep restarts the container.

The seeded season is anchored to the day `seed_demo` ran: one match is in
progress *today* and roughly 60 per cent of the calendar is behind it. Weeks
later that live match sits in the past. Re-run
`python manage.py seed_demo --flush` to move the season back onto the current
date.

## Deploying on Railway

Railway has no permanent free plan that fits this app: the trial gives $5 of
credit for 30 days, and the ongoing free plan's $1 monthly credit does not cover
a web service and a database together. Budget about $5 a month.

### First deploy

```bash
npm install --global @railway/cli
railway login
railway init
railway add --database postgres
```

Set the variables from the table below on the service (`railway variables --set
'KEY=value'`, or the dashboard), referencing the database as
`${{Postgres.DATABASE_URL}}`, then:

```bash
railway up
```

`railway.json` runs `migrate` followed by `seed_demo` as the pre-deploy command,
so a fresh database arrives populated. `seed_demo` is idempotent, so it is a
no-op on every later deploy; use `railway run python manage.py seed_demo --flush`
to rebuild the dataset deliberately.

`RAILWAY_PUBLIC_DOMAIN` is injected by the platform and picked up
automatically, so there is no second deploy just to register the hostname.

### Continuous deployment

A merge to `main` ships itself. Render watches the repository and, with
`autoDeployTrigger: checksPass`, waits for the GitHub checks on that commit
before building — so a red suite stops the deploy instead of shipping past it.

The `image` job in [CI](.github/workflows/ci.yml) builds the deployment
`Dockerfile` on every push. The unit suites can pass against source the image
still fails to build: `collectstatic` runs during the build with a deliberately
bare environment, and a settings change once broke it there and nowhere else.

The container applies migrations and seeds on start, so a schema change ships
with its own migration and needs no manual step.

> A service created directly from the repository rather than as a Blueprint does
> not read `render.yaml`. Set **Settings → Auto-Deploy → After CI Checks Pass**
> in the dashboard for that service.

### Production environment

| Variable | Required | Value |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | baked into the image | `config.settings.production` |
| `DJANGO_SECRET_KEY` | **yes** | A long random string. The process refuses to start without it. |
| `DJANGO_ALLOWED_HOSTS` | only for a custom domain | Public hostname, no scheme. The platform's own domain is picked up automatically. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | only for a custom domain | Public origin, with scheme. Same automatic pickup. |
| `DATABASE_URL` | **yes** | `${{Postgres.DATABASE_URL}}`. Overrides every `POSTGRES_*` value. |
| `PORT` | injected | Supplied by the platform; the image binds it. |
| `SPA_ROOT` | baked into the image | `/app/spa`. Unset it and Django serves the API only. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | no | Leave empty. Only needed if the SPA is hosted elsewhere. |
| `DJANGO_SECURE_SSL_REDIRECT` | no | Defaults to `true`. Only set `false` without TLS. |
| `DJANGO_SESSION_COOKIE_SECURE` | no | Defaults to `true`. |
| `DJANGO_CSRF_COOKIE_SECURE` | no | Defaults to `true`. |
| `DJANGO_HSTS_SECONDS` | no | Defaults to one year. |
| `REDIS_URL` | no | Absent: live updates are fanned out in-process and notification tasks run inline. |
| `WEB_CONCURRENCY` | no | Defaults to `1`. Raise it **only** alongside `REDIS_URL`. |
| `RUN_RELEASE_ON_START` | no | `true` makes the entrypoint run `migrate` and `seed_demo`. Needed where the platform has no release phase. |
| `DJANGO_LOG_LEVEL` | no | Defaults to `INFO`. |
| `VITE_DEMO_EMAIL` / `VITE_DEMO_PASSWORD` | build time | Credentials behind the one-click sign-in button; build with an empty email to hide it. |

The image trusts `X-Forwarded-Proto` for HTTPS detection, so the SSL redirect and
the `Secure` cookie flags behave correctly behind the platform's TLS proxy.

### Running the production image locally

```bash
docker build -t leaguehub .
docker run --rm -p 8088:8000 \
  -e DJANGO_SECRET_KEY=local-only \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8088 \
  -e DATABASE_URL=postgresql://leaguehub:leaguehub-local@host.docker.internal:5432/leaguehub \
  -e DJANGO_SECURE_SSL_REDIRECT=false \
  leaguehub
```

Run `python manage.py migrate && python manage.py seed_demo` in the container
first; the pre-deploy hook only runs on the platform.

### Nginx-fronted Compose profile

`compose.production.yml` runs the alternative topology — Nginx, Django on
Daphne, PostgreSQL, Redis and the Celery worker and beat as separate services:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f compose.production.yml up -d --build --wait
docker compose --env-file .env.production -f compose.production.yml exec backend python manage.py seed_demo
```

Open `http://localhost:8080`. Stop it without deleting named volumes with
`docker compose --env-file .env.production -f compose.production.yml down`.

## Verification

```bash
cd backend
uv run ruff check .
uv run python manage.py check
uv run pytest
uv run python manage.py makemigrations --check --dry-run

cd ../frontend
pnpm lint
pnpm test
pnpm e2e
pnpm build
```

Pytest uses an isolated in-memory SQLite database, so the unit tests need no
running service. GitHub Actions runs the backend checks, the frontend
lint/typecheck/unit tests and production build, plus the Playwright smoke test,
on every push and pull request to `main`.

## Repository layout

```text
leaguehub/
├── backend/                  Django project: apps, settings, tests
├── frontend/                 React SPA
├── docs/                     architecture, domain model, design, development log
├── Dockerfile                single-service production image
├── render.yaml               free deployment (Render + Neon)
├── railway.json              Railway deployment
├── compose.yml               local PostgreSQL and Redis
├── compose.production.yml    Nginx-fronted production profile
├── .env.example
└── .env.production.example
```
