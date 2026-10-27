"""Production hardening. Staging inherits this and relaxes only what it must."""

from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import (
    ALLOWED_HOSTS,
    BREVO_API_KEY,
    BREVO_MODE,
    CORS_ALLOWED_ORIGINS,
    DATABASES,
    EMAIL_BACKEND,
    FRONTEND_BASE_URL,
    STORAGES,
    env,
)

DEBUG = False

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_COOKIE_SECURE = True

# Set when TLS terminates at a proxy that sets this header, e.g. "HTTP_X_FORWARDED_PROTO,https".
_proxy_ssl_header = env.tuple("SECURE_PROXY_SSL_HEADER", default=())
if _proxy_ssl_header:
    SECURE_PROXY_SSL_HEADER = _proxy_ssl_header

# Links in emails (password reset, welcome) must point at the public site, never localhost.
# A localhost value usually means the local .env was copied to the host; prefer the URL the
# host itself reports (Render sets RENDER_EXTERNAL_URL) and otherwise refuse to start.
if urlparse(FRONTEND_BASE_URL).hostname in ("localhost", "127.0.0.1", "::1"):
    FRONTEND_BASE_URL = env("RENDER_EXTERNAL_URL", default="")
    if not FRONTEND_BASE_URL:
        raise ImproperlyConfigured(
            "FRONTEND_BASE_URL points at localhost; set it to the public site URL "
            "(e.g. https://edunextsl.onrender.com)."
        )

if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list explicit hosts (no '*').")
if "*" in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must not contain '*'.")
if BREVO_API_KEY and not BREVO_MODE:
    raise ImproperlyConfigured(
        "BREVO_API_KEY is an SMTP key (xsmtpsib-...), which cannot use Brevo's HTTP API. "
        "Create an API key (xkeysib-...) in Brevo > SMTP & API, or also set BREVO_SMTP_LOGIN."
    )
# Staging may run without a mail provider (password-reset links then go to the logs).
if env.bool("REQUIRE_REAL_EMAIL", default=True) and not BREVO_MODE and "console" in EMAIL_BACKEND:
    raise ImproperlyConfigured("Set BREVO_API_KEY (or EMAIL_URL) to send real email.")
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise ImproperlyConfigured("DATABASE_URL must point at PostgreSQL in production/staging.")

STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
