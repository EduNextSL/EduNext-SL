from django.conf import settings
from rest_framework.exceptions import PermissionDenied


class TrustedOriginMixin:
    """Reject browser requests whose Origin is not an allowed frontend origin.

    Protects cookie-bearing endpoints (login/refresh/logout) against cross-site
    request forgery regardless of the cookie SameSite setting. Requests without an
    Origin header (non-browser clients) are unaffected.
    """

    def initial(self, request, *args, **kwargs):
        origin = request.META.get("HTTP_ORIGIN")
        if origin and origin not in settings.CORS_ALLOWED_ORIGINS:
            raise PermissionDenied("Request origin is not allowed.")
        super().initial(request, *args, **kwargs)
