"""JSON replacements for Django's HTML 404/500 pages."""

from django.db import connection
from django.http import JsonResponse

from .exceptions import ErrorCode


def not_found(request, exception=None):
    return JsonResponse(
        {"success": False, "code": ErrorCode.NOT_FOUND, "message": "Not found.", "errors": {}},
        status=404,
    )


def server_error(request):
    return JsonResponse(
        {
            "success": False,
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "An unexpected error occurred.",
            "errors": {},
        },
        status=500,
    )


def health(request):
    """Liveness + database check for the load balancer / host health probe."""
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
