from .base import *  # noqa: F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=True)

# Plain HTTP on localhost, so the Secure cookie flag would make the cookie unusable.
AUTH_COOKIE_SECURE = env.bool("AUTH_COOKIE_SECURE", default=False)

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://localhost:3000"]
)
