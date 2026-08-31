"""Hardened settings for the containerized production-like deployment."""

import os

from .base import *  # noqa: F403
from .base import _env_bool, _env_list


DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", [])
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])
CORS_ALLOWED_ORIGINS = _env_list("DJANGO_CORS_ALLOWED_ORIGINS", [])

# These defaults are safe behind TLS. The local production Compose example
# explicitly disables redirects/cookie flags because it serves plain HTTP.
SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = _env_bool("DJANGO_SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = _env_bool("DJANGO_CSRF_COOKIE_SECURE", True)
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# WhiteNoise serves Django's own static files (admin, DRF, the schema UI) and,
# when SPA_ROOT is set, the compiled single-page app from the site root. Serving
# both from one origin is deliberate: it keeps the session and CSRF cookies
# first-party, which a split frontend/backend host on *.up.railway.app cannot do
# because that suffix makes the two subdomains cross-site.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_ROOT = SPA_ROOT  # noqa: F405
# index.html must never be cached, or a deploy leaves clients on a stale bundle
# whose hashed asset URLs no longer exist.
WHITENOISE_INDEX_FILE = True
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ["woff", "woff2", "gz", "br", "png", "jpg", "svg"]

# Without a Redis service there is nowhere to fan match updates out to, and no
# worker to run notifications. A single instance can do both in-process.
if not os.getenv("REDIS_URL"):
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
