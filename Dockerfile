# Single-service production image: the compiled SPA and the API ship together and
# are served from one origin, which keeps the session cookie first-party.
# backend/Dockerfile is the separate, nginx-fronted variant used by
# compose.production.yml; this one is what the managed platform builds.

FROM node:24-alpine AS frontend
WORKDIR /app
RUN npm install --global pnpm@10.30.2
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    SPA_ROOT=/app/spa \
    PATH="/app/backend/.venv/bin:$PATH"

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock /app/backend/
RUN pip install --no-cache-dir uv \
    && cd /app/backend \
    && uv sync --locked --no-dev

COPY backend /app/backend
RUN chmod +x /app/backend/docker-entrypoint.sh
COPY --from=frontend /app/dist /app/spa

WORKDIR /app/backend

# collectstatic needs the manifest storage to run, so give it the throwaway
# values the build has no business knowing. Nothing here reaches runtime.
RUN DJANGO_SECRET_KEY=build-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    DJANGO_SECURE_SSL_REDIRECT=false \
    python manage.py collectstatic --noinput --clear

# One worker by default: without a Redis channel layer, live match updates are
# fanned out in-process and a second worker would not see them. Set REDIS_URL
# and raise WEB_CONCURRENCY together, never one without the other.
ENV WEB_CONCURRENCY=1
EXPOSE 8000

# The entrypoint runs migrations and seeding when the platform has no release
# phase, then execs gunicorn. uvicorn workers keep this ASGI, so the match
# WebSocket still works under gunicorn.
CMD ["./docker-entrypoint.sh"]
