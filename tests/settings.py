"""Isolated pytest settings: inherit app settings, force SQLite test DB."""
from forex_web.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Avoid sending real transactional mail during tests.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
