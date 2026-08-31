FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock /app/backend/
RUN pip install --no-cache-dir uv \
    && cd /app/backend \
    && uv sync --locked --no-dev

COPY backend /app/backend
WORKDIR /app/backend
ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
