# Development log

LeagueHub was built in numbered stages. The notes below are the stage
descriptions as they were written at the time, moved here from the README so
that the README can describe the application as it stands rather than how it
arrived. For what the application does today, see the
[README](../README.md).

## Stage 00–05 — foundations, authentication, competition domain

The backend foundation, Django session authentication, multi-tenant
organizations/RBAC, the league competition domain, deterministic round-robin
fixture generation, match lifecycle events, and derived standings/statistics.

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

## Stage 06 — match lifecycle and events

Stage 6 adds the match lifecycle and match events. A fixture can have one
`Match`, whose state moves through explicit transitions such as `SCHEDULED`,
`LIVE`, `FINISHED`, `CANCELLED`, and `POSTPONED`. Events are accepted only for
live matches, and a goal updates the corresponding home or away score in the
same database transaction as the event. Players must be rostered for the
fixture's season and team. Match and event routes are nested under the same
organization/league/season scope and manager writes are enforced server-side.

## Stage 07 — standings and statistics

Stage 7 adds derived season standings at `standings/` using only `FINISHED`
matches and the 3/1/0 scoring system. Rows are ordered by points, goal
difference, goals for, team name, and team ID. Player statistics and the top
scorers list are available under `statistics/players/` and
`statistics/top-scorers/`; they aggregate finished-match goals and cards from
`MatchEvent`. Appearances are intentionally not reported yet because the
domain does not store lineups or minutes played. Aggregation queries use
related filters and dedicated indexes to avoid N+1 event lookups.

## Stage 08 — REST API hardening

Stage 8 hardens collection endpoints with optional page-number pagination.
Add `page=1&page_size=20` to receive `count`, `next`, `previous`, and
`results`; without those parameters, the existing list response remains
available. Organizations, leagues, seasons, teams, players, rosters, fixtures,
matches, standings, and player statistics support safe search/order options
where they are meaningful. Match collections also accept comma-separated
status filters. Invalid query parameters and other API exceptions use a
consistent `detail`, `code`, and (for validation) `fields` response shape.

## Stage 09 — React authentication foundation

Stage 9 adds the React authentication foundation. The SPA uses React Router,
TanStack Query, and a small fetch-based API client. Session cookies are sent
with `credentials: include`; mutating requests first obtain the Django CSRF
cookie and echo it in `X-CSRFToken`. The public routes are `/login` and
`/register`; authenticated users are redirected to `/dashboard`, where their
organizations are loaded from the API. Vite proxies `/api` to the local Django
server during development.

## Stage 10 — league management UI

Stage 10 adds the league-management UI. From the dashboard, an authenticated
user can create an organization and open it to view and manage leagues,
seasons, teams, players, seasonal team assignments, and rosters. Manager-only
forms use React Hook Form with Zod schemas for immediate client-side feedback;
the API remains the source of truth and performs its own validation and
authorization. TanStack Query owns server state, scopes cache keys by
organization/league/season/team IDs, and invalidates the affected collection
after each successful mutation. The page explicitly handles loading, error,
and empty states for every collection.

## Stage 11 — league dashboard

Stage 11 adds the league dashboard at `/leagues/:leagueId`. The dashboard keeps
the organization and selected season in the URL, then uses TanStack Query to
load league information, fixtures, matches, standings, teams, and player
statistics. Its overview highlights upcoming fixtures, recent results, the
table, and top scorers; dedicated routes expose fixtures, table, teams,
statistics, and match detail views. These are read-only views over the existing
REST API; live updates are intentionally deferred to the WebSocket work in
Stage 12.

## Stage 12 — live match center

Stage 12 adds the live match center. Django Channels exposes an authenticated
WebSocket at the match scope, while HTTP remains responsible for lifecycle
commands and event mutations. Successful match creation, transitions, and
events schedule a post-commit snapshot for the Redis channel group, so a
failed transaction is never broadcast. The React match view subscribes to the
socket, updates the TanStack Query match/event cache, displays connection
status, and retries with exponential backoff after a disconnect. The Vite
development proxy forwards `/ws` to the ASGI server.

## Stage 13 — background jobs and notifications

Stage 13 adds background jobs and in-app notifications. Celery uses Redis as
its broker and result backend; Celery Beat scans a small 24-hour window every
15 minutes for scheduled-match reminders. Finishing a match enqueues a
post-match notification after the database transaction commits. Notification
dedupe keys make task delivery idempotent, and only transient connection or
timeout errors are eligible for bounded retry. Authenticated users can read
their own notifications at `/api/v1/notifications/` and mark them as read;
the React shell exposes the same data in a small notification menu.

## Stage 14–15 — testing, CI, production profile

Automated backend and frontend test suites with a Playwright smoke test, run by
GitHub Actions on every push and pull request to `main`, followed by a
production-like Docker profile with Nginx, secure environment-driven settings,
health checks, and an idempotent demo data command.

## Stage 16 — reverted

An optional match-report feature was added and reverted the same day
(`5d2cef4`, reverted by `fb239a4`). It is not part of the application.

## After the stages

Later work is recorded in the commit history rather than as numbered stages: a
realistic `seed_demo` dataset, one-click demo sign-in, a design system applied
across every view (see [DESIGN.md](DESIGN.md)), and the single-service
production deployment configuration.
