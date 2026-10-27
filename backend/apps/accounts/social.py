"""Social sign-in: provider credential verification.

Each provider implements `SocialIdentityVerifier`. The credential comes from the
browser but is never trusted: the verifier validates it cryptographically (signature,
audience, expiry) before any account is touched.
"""

import hashlib
import hmac
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
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


class SocialEmailRequired(ApiError):
    status_code = 400
    error_code = "SOCIAL_EMAIL_REQUIRED"
    default_detail = (
        "Facebook did not share an email address with us. Allow email access when signing in, "
        "or use a Facebook account that has a confirmed email."
    )

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


class FacebookVerifier(SocialIdentityVerifier):
    """Verifies a Facebook Login user access token with Facebook's Graph API.

    The token is checked as issued to *this* app (debug_token), then the profile is read
    server-side; nothing the browser says about the user is trusted.
    """

    GRAPH = "https://graph.facebook.com"
    TIMEOUT_SECONDS = 10

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    def _get(self, path: str, params: dict) -> dict:
        try:
            response = requests.get(
                f"{self.GRAPH}{path}", params=params, timeout=self.TIMEOUT_SECONDS
            )
            body = response.json()
        except (requests.RequestException, ValueError):
            raise SocialAuthError from None
        if response.status_code != 200 or not isinstance(body, dict):
            raise SocialAuthError
        return body

    def verify(self, credential: str) -> SocialIdentity:
        app_token = f"{self.app_id}|{self.app_secret}"
        debug = self._get("/debug_token", {"input_token": credential, "access_token": app_token})
        data = debug.get("data") or {}
        if (
            data.get("is_valid") is not True
            or str(data.get("app_id")) != self.app_id
            or not data.get("user_id")
        ):
            raise SocialAuthError

        proof = hmac.new(self.app_secret.encode(), credential.encode(), hashlib.sha256).hexdigest()
        profile = self._get(
            "/me",
            {
                "fields": "id,first_name,last_name,email",
                "access_token": credential,
                "appsecret_proof": proof,
            },
        )
        if str(profile.get("id")) != str(data["user_id"]):
            raise SocialAuthError
        if not profile.get("email"):
            raise SocialEmailRequired
        return SocialIdentity(
            provider=SocialProvider.FACEBOOK,
            subject=str(profile["id"]),
            email=normalize_email(profile["email"]),
            first_name=profile.get("first_name", ""),
            last_name=profile.get("last_name", ""),
        )


def get_verifier(provider: str) -> SocialIdentityVerifier | None:
    """Verifier for a provider, or None while it is not configured."""
    if provider == SocialProvider.GOOGLE and settings.GOOGLE_OAUTH_CLIENT_ID:
        return GoogleVerifier(settings.GOOGLE_OAUTH_CLIENT_ID)
    if (
        provider == SocialProvider.FACEBOOK
        and settings.FACEBOOK_APP_ID
        and settings.FACEBOOK_APP_SECRET
    ):
        return FacebookVerifier(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
    return None
