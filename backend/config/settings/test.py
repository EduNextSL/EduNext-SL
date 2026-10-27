"""Settings for the automated test suite.

Uses PostgreSQL when DATABASE_URL is set, otherwise falls back to in-memory SQLite
so the suite runs anywhere. No real secrets live here.
"""

import os

os.environ["EDUNEXT_SKIP_DOTENV"] = "1"
os.environ.setdefault(
    "DJANGO_SECRET_KEY", "test-only-secret-key-not-for-any-real-environment-0123456789"
)
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .base import *  # noqa: E402, F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
API_DOCS_ENABLED = True
AUTH_COOKIE_SECURE = False
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
FRONTEND_BASE_URL = "http://localhost:5173"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # speed only

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        scope: "10000/minute"
        for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]  # noqa: F405
    },
}

# The suite must never reach real services, whatever .env contains.
BREVO_API_KEY = ""
BREVO_MODE = ""
EMAIL_SENDER_CLASS = "apps.core.email.DjangoEmailSender"
EMAIL_ASYNC = False
CLOUDINARY_NAME = CLOUDINARY_API_KEY = CLOUDINARY_API_SECRET = ""
CLOUDINARY_ENABLED = False
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
GOOGLE_OAUTH_CLIENT_ID = ""
FACEBOOK_APP_ID = ""
FACEBOOK_APP_SECRET = ""
EMAIL_LOGO_URL = ""
