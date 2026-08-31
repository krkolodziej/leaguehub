"""Development settings used by manage.py and the local server."""

from .base import *  # noqa: F403
from .base import CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS

DEBUG = True

# The SPA runs on its own port and proxies /api to this server, so every
# state-changing request arrives cross-origin and Django's CSRF origin check
# rejects it unless the Vite origin is trusted. Production still requires
# DJANGO_CSRF_TRUSTED_ORIGINS to be set explicitly; locally we default to the
# same origins CORS already allows, so `manage.py runserver` works on its own.
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)
