import importlib
from pathlib import Path

import pytest
from django.test import override_settings
from django.urls import clear_url_caches, resolve, reverse


PRODUCTION_ENV = {
    "DJANGO_SECRET_KEY": "test-only",
    "DJANGO_ALLOWED_HOSTS": "leaguehub.example",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://leaguehub.example",
}


@pytest.fixture
def production(monkeypatch):
    for key, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return importlib.reload(importlib.import_module("config.settings.production"))


def test_production_is_locked_down(production):
    assert production.DEBUG is False
    assert production.ALLOWED_HOSTS == ["leaguehub.example"]
    assert production.CSRF_TRUSTED_ORIGINS == ["https://leaguehub.example"]
    assert production.SESSION_COOKIE_SECURE is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SESSION_COOKIE_HTTPONLY is True
    assert production.SECURE_SSL_REDIRECT is True
    # The platform terminates TLS, so HTTPS is only visible via the proxy header.
    assert production.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_whitenoise_serves_static_ahead_of_everything_but_security(production):
    security = production.MIDDLEWARE.index(
        "django.middleware.security.SecurityMiddleware"
    )
    whitenoise = production.MIDDLEWARE.index(
        "whitenoise.middleware.WhiteNoiseMiddleware"
    )
    assert whitenoise == security + 1
    assert "whitenoise" in production.STORAGES["staticfiles"]["BACKEND"]


def test_single_instance_falls_back_to_in_process_delivery(production):
    """No Redis means no worker and no cross-process fan-out; do both inline."""
    assert production.CHANNEL_LAYERS["default"]["BACKEND"] == (
        "channels.layers.InMemoryChannelLayer"
    )
    assert production.CELERY_TASK_ALWAYS_EAGER is True


def test_database_url_overrides_the_discrete_postgres_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example:6543/leaguehub")
    base = importlib.reload(importlib.import_module("config.settings.base"))

    assert base.DATABASES["default"]["HOST"] == "db.example"
    assert base.DATABASES["default"]["PORT"] == 6543
    assert base.DATABASES["default"]["NAME"] == "leaguehub"


@pytest.mark.django_db
def test_spa_routes_fall_through_to_index_without_shadowing_the_api(tmp_path, client):
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>", encoding="utf-8")

    with override_settings(SPA_ROOT=str(tmp_path), ROOT_URLCONF="config.urls"):
        clear_url_caches()
        importlib.reload(importlib.import_module("config.urls"))

        # A client-side route returns the shell rather than a 404.
        assert client.get("/leagues/1/table").status_code == 200
        # while the API and admin keep their own handlers.
        assert resolve("/api/v1/health/").func.__name__ != "SpaIndexView"
        assert client.get("/api/v1/does-not-exist/").status_code == 404

    clear_url_caches()
    importlib.reload(importlib.import_module("config.urls"))


def test_spa_index_view_is_absent_when_no_build_is_bundled():
    from django.conf import settings

    assert settings.SPA_ROOT is None
    with pytest.raises(Exception):
        reverse("spa-index")


def test_dockerfile_and_railway_config_agree_on_the_release_step():
    root = Path(__file__).resolve().parents[4]
    railway = (root / "railway.json").read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

    assert "migrate --noinput" in railway and "seed_demo" in railway
    assert "gunicorn" in dockerfile
    assert "uvicorn.workers.UvicornWorker" in dockerfile
    assert "SPA_ROOT=/app/spa" in dockerfile
