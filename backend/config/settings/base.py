"""Settings shared by every environment. Environment modules override as needed."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

# --- Core -------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.companies",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://edunext")}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=False)

# --- Authentication ---------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.ActiveAccountBackend"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    # Fallbacks keep verifying (and transparently upgrading) older hashes.
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": env.int("PASSWORD_MIN_LENGTH", default=10)},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Password reset links are valid for this many seconds and are single-use
# (Django's token generator hashes the current password, so changing it voids the link).
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT_SECONDS", default=3600)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=10)),
    # Longest possible refresh lifetime; shorter "session" tokens are trimmed in
    # apps.accounts.tokens so the stored OutstandingToken never expires early.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_REMEMBER_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Refresh tokens live in an HttpOnly cookie; the access token is returned in the
# JSON body and kept in memory by the SPA.
AUTH_COOKIE_NAME = env("AUTH_COOKIE_NAME", default="edunext_refresh")
AUTH_COOKIE_PATH = "/api/v1/auth/"
AUTH_COOKIE_DOMAIN = env("AUTH_COOKIE_DOMAIN", default=None)
AUTH_COOKIE_SECURE = env.bool("AUTH_COOKIE_SECURE", default=True)
AUTH_COOKIE_SAMESITE = env("AUTH_COOKIE_SAMESITE", default="Lax")
AUTH_REFRESH_SESSION_HOURS = env.int("JWT_REFRESH_SESSION_HOURS", default=24)

# Legal acceptance: versions are configured, never invented in code.
LEGAL_TERMS_VERSION = env("LEGAL_TERMS_VERSION", default="unspecified")
LEGAL_USER_AGREEMENT_VERSION = env("LEGAL_USER_AGREEMENT_VERSION", default="unspecified")
LEGAL_PRIVACY_POLICY_VERSION = env("LEGAL_PRIVACY_POLICY_VERSION", default="unspecified")

# --- REST framework ---------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.ActiveUserJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_RATE_ANON", default="1000/hour"),
        "user": env("THROTTLE_RATE_USER", default="2000/hour"),
        "register": env("THROTTLE_RATE_REGISTER", default="10/hour"),
        "login": env("THROTTLE_RATE_LOGIN", default="20/minute"),
        "login_identity": env("THROTTLE_RATE_LOGIN_IDENTITY", default="10/minute"),
        "password_reset_request": env("THROTTLE_RATE_PASSWORD_RESET_REQUEST", default="5/hour"),
        "password_reset_confirm": env("THROTTLE_RATE_PASSWORD_RESET_CONFIRM", default="10/hour"),
        "token_refresh": env("THROTTLE_RATE_TOKEN_REFRESH", default="60/minute"),
        "social_login": env("THROTTLE_RATE_SOCIAL_LOGIN", default="20/minute"),
    },
    # Number of reverse proxies in front of Django (0 = trust REMOTE_ADDR only).
    "NUM_PROXIES": env.int("TRUSTED_PROXY_COUNT", default=0),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "EduNext SL API",
    "DESCRIPTION": (
        "Authentication foundation for EduNext SL.\n\n"
        "Successful responses use `{success: true, message?, data}`; errors use "
        "`{success: false, code, message, errors}`.\n\n"
        "Send the access token as `Authorization: Bearer <token>`. The refresh token "
        "is an HttpOnly cookie set by login/refresh; call those endpoints with "
        "`credentials: 'include'`."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- CORS / CSRF ------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --- Security headers (always on) -------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --- Email ------------------------------------------------------------------

_email = env.email("EMAIL_URL", default="consolemail://")
EMAIL_BACKEND = _email["EMAIL_BACKEND"]
EMAIL_HOST = _email.get("EMAIL_HOST", "")
EMAIL_PORT = _email.get("EMAIL_PORT", 25)
EMAIL_HOST_USER = _email.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = _email.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _email.get("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = _email.get("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="EduNext SL <no-reply@example.com>")
EMAIL_SENDER_CLASS = "apps.core.email.DjangoEmailSender"

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")
FRONTEND_PASSWORD_RESET_PATH = env("FRONTEND_PASSWORD_RESET_PATH", default="/reset-password")

# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
