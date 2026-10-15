"""Integration boundary for Google / Facebook sign-in.

Nothing is wired yet: provider credentials and the product's account-linking rules
are undecided. When they are, implement `SocialIdentityVerifier` for a provider
(verify the provider's ID/access token server-side, never trust client-supplied
profile data) and register it in `_VERIFIERS`. The view, throttle and URL already
exist, so no other code changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class SocialProvider:
    GOOGLE = "google"
    FACEBOOK = "facebook"
    ALL = (GOOGLE, FACEBOOK)


@dataclass(frozen=True)
class SocialIdentity:
    provider: str
    subject: str  # provider's stable user id
    email: str
    email_verified: bool


class SocialIdentityVerifier(ABC):
    @abstractmethod
    def verify(self, credential: str) -> SocialIdentity:
        """Validate the provider credential with the provider; raise on failure."""


_VERIFIERS: dict[str, SocialIdentityVerifier] = {}


def get_verifier(provider: str) -> SocialIdentityVerifier | None:
    return _VERIFIERS.get(provider)
