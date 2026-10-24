"""Refresh/access token lifecycle built on djangorestframework-simplejwt.

Refresh tokens are single-use: every refresh blacklists the presented token and issues
a new one. Presenting an already-used token signals theft, so all of that user's
refresh tokens are revoked. No cryptography is implemented here.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.audit import record_event
from apps.core.exceptions import ApiError, ErrorCode
from apps.core.models import AuditEvent
from apps.core.utils import RequestMeta

from .models import User

REMEMBER_ME_CLAIM = "rm"


class InvalidRefreshToken(ApiError):
    status_code = 401
    error_code = ErrorCode.INVALID_REFRESH_TOKEN
    default_detail = "Refresh token is invalid or has expired."

    def __init__(self):
        super().__init__(self.default_detail)


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str
    remember_me: bool
    refresh_lifetime: timedelta
    access_expires_in: int  # seconds


def _refresh_lifetime(remember_me: bool) -> timedelta:
    if remember_me:
        return api_settings.REFRESH_TOKEN_LIFETIME
    return timedelta(hours=settings.AUTH_REFRESH_SESSION_HOURS)


def _build_pair(refresh: RefreshToken, remember_me: bool) -> TokenPair:
    lifetime = _refresh_lifetime(remember_me)
    refresh[REMEMBER_ME_CLAIM] = remember_me
    refresh.set_exp(lifetime=lifetime)
    access = refresh.access_token
    access.payload.pop(REMEMBER_ME_CLAIM, None)
    return TokenPair(
        access=str(access),
        refresh=str(refresh),
        remember_me=remember_me,
        refresh_lifetime=lifetime,
        access_expires_in=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
    )


def issue_tokens(user: User, *, remember_me: bool) -> TokenPair:
    return _build_pair(RefreshToken.for_user(user), remember_me)


def revoke_all_user_tokens(user: User) -> None:
    """Blacklist every outstanding refresh token for the user (all devices)."""
    live = OutstandingToken.objects.filter(user=user).exclude(blacklistedtoken__isnull=False)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in live], ignore_conflicts=True
    )


def revoke_refresh_token(raw_token: str) -> User | None:
    """Blacklist one refresh token (logout). Returns its user, or None if unusable."""
    try:
        token = RefreshToken(raw_token)
        user = User.objects.filter(pk=token[api_settings.USER_ID_CLAIM]).first()
        token.blacklist()
    except TokenError:
        return None
    return user


def rotate_refresh_token(raw_token: str, meta: RequestMeta) -> TokenPair:
    """Exchange a valid refresh token for a new pair; detect and punish reuse."""
    try:
        old = RefreshToken(raw_token)
    except TokenError:
        _handle_possible_reuse(raw_token, meta)
        raise InvalidRefreshToken from None

    reused_by: User | None = None
    with transaction.atomic():
        # Row lock serialises concurrent refreshes with the same token: the loser
        # sees it blacklisted and is treated as reuse.
        outstanding = (
            # of=("self",): PostgreSQL cannot lock the nullable (outer-joined) user side.
            OutstandingToken.objects.select_for_update(of=("self",))
            .select_related("user")
            .filter(jti=old["jti"])
            .first()
        )
        if outstanding is None or outstanding.user is None:
            raise InvalidRefreshToken
        user = outstanding.user
        if BlacklistedToken.objects.filter(token=outstanding).exists():
            reused_by = user
        elif not user.can_authenticate:
            raise InvalidRefreshToken
        else:
            BlacklistedToken.objects.create(token=outstanding)
            pair = _build_pair(
                RefreshToken.for_user(user), remember_me=bool(old.payload.get(REMEMBER_ME_CLAIM))
            )

    if reused_by is not None:
        _revoke_after_reuse(reused_by, meta)
        raise InvalidRefreshToken
    return pair


def _handle_possible_reuse(raw_token: str, meta: RequestMeta) -> None:
    """A rejected token that is still correctly signed and unexpired was blacklisted: reuse."""
    try:
        payload = token_backend.decode(raw_token, verify=True)
    except TokenBackendError:
        return
    jti = payload.get(api_settings.JTI_CLAIM)
    if not BlacklistedToken.objects.filter(token__jti=jti).exists():
        return
    user = User.objects.filter(pk=payload.get(api_settings.USER_ID_CLAIM)).first()
    if user is not None:
        _revoke_after_reuse(user, meta)


def _revoke_after_reuse(user: User, meta: RequestMeta) -> None:
    revoke_all_user_tokens(user)
    record_event(AuditEvent.REFRESH_TOKEN_REUSE, actor=user, meta=meta)
