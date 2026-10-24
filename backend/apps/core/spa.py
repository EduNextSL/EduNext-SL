"""Serve the built React app and fall back to index.html for client-side routes."""

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_safe


@require_safe
def spa_index(request, path: str = ""):
    index = settings.FRONTEND_DIST_DIR / "index.html"
    if not index.is_file():
        return HttpResponse(
            "Frontend build not found. Run `npm run build` in the frontend project.",
            status=503,
            content_type="text/plain",
        )
    response = HttpResponse(index.read_bytes(), content_type="text/html; charset=utf-8")
    # index.html names the current hashed assets, so it must always be revalidated.
    response["Cache-Control"] = "no-cache"
    return response
