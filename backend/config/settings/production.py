"""Production hardening. Staging inherits this and relaxes only what it must."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, EMAIL_BACKEND, env

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

if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list explicit hosts (no '*').")
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must list the React app origin(s).")
if "console" in EMAIL_BACKEND:
    raise ImproperlyConfigured("EMAIL_URL must point at a real email provider.")
