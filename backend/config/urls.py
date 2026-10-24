import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.spa import spa_index
from apps.core.views import health

handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/health/", health, name="health"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/media/", include("apps.media.urls")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]

# Everything else is a React route. API, admin and asset paths are excluded so that a
# missing JS chunk or unknown API path is a real 404 instead of an HTML page.
_reserved = "|".join(
    re.escape(prefix.strip("/")) for prefix in ("api", settings.ADMIN_URL, "assets", "static")
)
urlpatterns.append(re_path(rf"^(?!(?:{_reserved})(?:/|$))(?P<path>.*)$", spa_index, name="spa"))
