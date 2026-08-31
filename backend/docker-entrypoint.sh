#!/bin/sh
set -e

# Platforms that have no release phase — or whose release phase is a paid
# feature, as on Render's free instances — set RUN_RELEASE_ON_START=true and get
# the same work done here instead. Both commands are safe to repeat: migrate is
# a no-op once applied, and seed_demo refuses to touch an already-seeded
# database unless --flush is passed.
if [ "${RUN_RELEASE_ON_START}" = "true" ]; then
    echo "release: applying migrations"
    python manage.py migrate --noinput
    echo "release: seeding demonstration data"
    python manage.py seed_demo
fi

exec gunicorn config.asgi:application \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
