from django.conf import settings
from rest_framework.response import Response

from .tokens import TokenPair


def set_refresh_cookie(response: Response, pair: TokenPair) -> None:
    """Attach the refresh token as an HttpOnly cookie.

    Remember-me gets a persistent cookie; otherwise a browser-session cookie.
    """
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        pair.refresh,
        max_age=int(pair.refresh_lifetime.total_seconds()) if pair.remember_me else None,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def read_refresh_cookie(request) -> str | None:
    return request.COOKIES.get(settings.AUTH_COOKIE_NAME) or None
