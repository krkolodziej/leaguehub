import importlib
from pathlib import Path

import pytest
from django.test import override_settings
from django.urls import clear_url_caches, resolve, reverse


PRODUCTION_ENV = {
    "DJANGO_SECRET_KEY": "test-only",
    "DJANGO_ALLOWED_HOSTS": "leaguehub.example",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://leaguehub.example",
    # Stands in for the Compose path, where the database arrives as discrete
    # variables rather than as one URL.
    "POSTGRES_HOST": "db.example",
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

    entrypoint = (root / "backend" / "docker-entrypoint.sh").read_text(encoding="utf-8")

    assert "migrate --noinput" in railway and "seed_demo" in railway
    assert "docker-entrypoint.sh" in dockerfile
    assert "SPA_ROOT=/app/spa" in dockerfile
    # ASGI under gunicorn, so the live-match WebSocket survives.
    assert "uvicorn.workers.UvicornWorker" in entrypoint


@pytest.mark.parametrize(
    "platform_var,hostname",
    [
        ("RENDER_EXTERNAL_HOSTNAME", "leaguehub.onrender.com"),
        ("RAILWAY_PUBLIC_DOMAIN", "leaguehub.up.railway.app"),
    ],
)
def test_platform_hostname_is_adopted_without_a_second_deploy(
    monkeypatch, platform_var, hostname
):
    """A host is only minted once the service exists, so read it back from the
    platform rather than making the operator deploy, copy it, and deploy again."""
    for key, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME", raising=False)
    monkeypatch.delenv("RAILWAY_PUBLIC_DOMAIN", raising=False)
    monkeypatch.setenv(platform_var, hostname)

    production = importlib.reload(importlib.import_module("config.settings.production"))

    assert hostname in production.ALLOWED_HOSTS
    assert f"https://{hostname}" in production.CSRF_TRUSTED_ORIGINS
    # Anything set by hand survives alongside it.
    assert "leaguehub.example" in production.ALLOWED_HOSTS


def test_release_step_runs_from_the_entrypoint_when_the_platform_lacks_one():
    root = Path(__file__).resolve().parents[4]
    entrypoint = (root / "backend" / "docker-entrypoint.sh").read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

    assert 'RUN_RELEASE_ON_START' in entrypoint
    assert "migrate --noinput" in entrypoint and "seed_demo" in entrypoint
    # exec, so gunicorn keeps PID 1 and receives the platform's stop signal.
    assert "exec gunicorn" in entrypoint
    assert "docker-entrypoint.sh" in dockerfile


def test_render_blueprint_targets_the_free_plan_and_seeds_on_start():
    root = Path(__file__).resolve().parents[4]
    blueprint = (root / "render.yaml").read_text(encoding="utf-8")

    assert "plan: free" in blueprint
    assert "runtime: docker" in blueprint
    assert "healthCheckPath: /api/v1/health/" in blueprint
    assert "RUN_RELEASE_ON_START" in blueprint
    # The database is deliberately not a Render one: a free Render Postgres is
    # deleted 30 days after creation.
    assert "databases:" not in blueprint


@pytest.mark.parametrize(
    "missing_var", ["DJANGO_SECRET_KEY", "DATABASE_URL"]
)
def test_missing_configuration_fails_with_a_readable_message(monkeypatch, missing_var):
    """A KeyError inside gunicorn's import stack reads as a crash, not as a
    configuration mistake. It cost a failed deploy to find that out."""
    from django.core.exceptions import ImproperlyConfigured

    for key, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example:5432/x")
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv(missing_var, raising=False)

    with pytest.raises(ImproperlyConfigured) as failure:
        importlib.reload(importlib.import_module("config.settings.production"))

    assert missing_var in str(failure.value)
    assert "README" in str(failure.value)

    monkeypatch.setenv(missing_var, PRODUCTION_ENV.get(missing_var, "postgresql://u:p@h:5432/x"))
    importlib.reload(importlib.import_module("config.settings.production"))
