import importlib


def test_development_trusts_the_spa_origin_without_extra_environment():
    """`manage.py runserver` must accept the Vite dev server's POSTs as shipped.

    Without this, sign-in and sign-out fail with "Origin checking failed" for
    anyone who starts the backend without exporting the example environment.
    """
    development = importlib.import_module("config.settings.development")

    assert development.CSRF_TRUSTED_ORIGINS, "development must trust some origin"
    assert "http://localhost:5173" in development.CSRF_TRUSTED_ORIGINS
    assert set(development.CORS_ALLOWED_ORIGINS).issubset(
        set(development.CSRF_TRUSTED_ORIGINS)
    )
