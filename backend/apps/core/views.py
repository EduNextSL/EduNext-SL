"""JSON replacements for Django's HTML 404/500 pages."""

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
