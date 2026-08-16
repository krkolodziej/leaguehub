"""Fast, isolated settings used by pytest."""

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "stage-01-test-only"
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
