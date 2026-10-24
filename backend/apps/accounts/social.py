"""Social sign-in: provider credential verification.

Each provider implements `SocialIdentityVerifier`. The credential comes from the
browser but is never trusted: the verifier validates it cryptographically (signature,
audience, expiry) before any account is touched. Facebook is not implemented yet.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from apps.core.exceptions import ApiError

from .validators import normalize_email


class SocialProvider:
    GOOGLE = "google"
    FACEBOOK = "facebook"
    ALL = (GOOGLE, FACEBOOK)


class SocialAuthError(ApiError):
    status_code = 401
    error_code = "SOCIAL_AUTH_FAILED"
    default_detail = "We could not verify your sign-in with the provider."

    def __init__(self):
        super().__init__(self.default_detail)


@dataclass(frozen=True)
class SocialIdentity:
    provider: str
    subject: str  # provider's stable user id
    email: str
    first_name: str = ""
    last_name: str = ""


class SocialIdentityVerifier(ABC):
    @abstractmethod
    def verify(self, credential: str) -> SocialIdentity:
        """Validate the provider credential; raise SocialAuthError on any failure."""


class GoogleVerifier(SocialIdentityVerifier):
    """Verifies a Google Identity Services ID token for this app's OAuth client ID."""

    def __init__(self, client_id: str):
        self.client_id = client_id

    def verify(self, credential: str) -> SocialIdentity:
        try:
            claims = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                self.client_id,
                clock_skew_in_seconds=10,
            )
        except (ValueError, GoogleAuthError):
            raise SocialAuthError from None
        # Only trust an email that Google itself has verified.
        if (
            not claims.get("sub")
            or not claims.get("email")
            or claims.get("email_verified") is not True
        ):
            raise SocialAuthError
        return SocialIdentity(
            provider=SocialProvider.GOOGLE,
            subject=claims["sub"],
            email=normalize_email(claims["email"]),
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
        )


def get_verifier(provider: str) -> SocialIdentityVerifier | None:
    """Verifier for a provider, or None while it is not configured."""
    if provider == SocialProvider.GOOGLE and settings.GOOGLE_OAUTH_CLIENT_ID:
        return GoogleVerifier(settings.GOOGLE_OAUTH_CLIENT_ID)
    return None
