from .base import env
from .production import *  # noqa: F403

API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
