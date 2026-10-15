"""Per-scope throttles for abuse-prone endpoints. Rates come from REST_FRAMEWORK settings."""

import hashlib

from rest_framework.throttling import SimpleRateThrottle


class IPScopedThrottle(SimpleRateThrottle):
    """Throttle by client IP under a named scope."""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class RegistrationThrottle(IPScopedThrottle):
    scope = "register"


class LoginThrottle(IPScopedThrottle):
    scope = "login"


class LoginIdentityThrottle(SimpleRateThrottle):
    """Throttle by target email (hashed) to slow credential stuffing from many IPs."""

    scope = "login_identity"

    def get_cache_key(self, request, view):
        email = request.data.get("email") if hasattr(request.data, "get") else None
        if not isinstance(email, str) or not email.strip():
            return None
        ident = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class PasswordResetRequestThrottle(IPScopedThrottle):
    scope = "password_reset_request"


class PasswordResetConfirmThrottle(IPScopedThrottle):
    scope = "password_reset_confirm"


class TokenRefreshThrottle(IPScopedThrottle):
    scope = "token_refresh"


class SocialLoginThrottle(IPScopedThrottle):
    scope = "social_login"
