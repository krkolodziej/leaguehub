# Interview notes

## Why production settings fail fast

`DJANGO_SECRET_KEY` is required when `config.settings.production` is loaded.
Hosts, trusted origins, cookie flags, HSTS, and logging are explicit environment
configuration rather than hidden code defaults.

## Why Nginx is in front

It serves the compiled SPA, supports history fallback, proxies HTTP and
WebSocket traffic, and gives health probes a tiny independent endpoint.

## How to demonstrate the app

Start the production-like Compose profile, run `seed_demo`, open the frontend,
sign in as `demo@example.com`, and browse the seeded league dashboard, fixtures,
finished matches, standings, and notifications.

## Operational boundaries

Migrations and static collection run before the backend starts. Celery worker
and beat are separate processes. Media is mounted on a named volume; static
files are collected into the image and served by Django/Nginx as the deployment
evolves.
