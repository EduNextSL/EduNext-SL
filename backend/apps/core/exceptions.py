"""One error shape for the whole API: {"success": false, "code", "message", "errors"}."""

import logging

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    INVALID_RESET_TOKEN = "INVALID_RESET_TOKEN"
    THROTTLED = "THROTTLED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApiError(exceptions.APIException):
    """Domain error carrying its own machine-readable code."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BAD_REQUEST

    def __init__(self, message: str | None = None, *, errors: dict | None = None):
        super().__init__(detail=message)
        self.errors = errors or {}


_CODE_BY_EXCEPTION = (
    (exceptions.ValidationError, ErrorCode.VALIDATION_ERROR),
    (exceptions.NotAuthenticated, ErrorCode.NOT_AUTHENTICATED),
    (exceptions.AuthenticationFailed, ErrorCode.AUTHENTICATION_FAILED),
    (exceptions.PermissionDenied, ErrorCode.PERMISSION_DENIED),
    (exceptions.NotFound, ErrorCode.NOT_FOUND),
    (exceptions.MethodNotAllowed, ErrorCode.METHOD_NOT_ALLOWED),
    (exceptions.UnsupportedMediaType, ErrorCode.UNSUPPORTED_MEDIA_TYPE),
    (exceptions.Throttled, ErrorCode.THROTTLED),
    (exceptions.ParseError, ErrorCode.BAD_REQUEST),
)

# Token-library errors carry internals (token class, claims); expose a fixed message instead.
_AUTH_FAILED_MESSAGE = "Authentication credentials are invalid or have expired."


def _code_for(exc: Exception) -> str:
    if isinstance(exc, ApiError):
        return exc.error_code
    for exc_type, code in _CODE_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            return code
    return ErrorCode.BAD_REQUEST


def _error_body(exc: Exception, code: str) -> dict:
    if isinstance(exc, exceptions.ValidationError):
        detail = exc.detail
        errors = detail if isinstance(detail, dict) else {"non_field_errors": detail}
        return {"message": "Validation failed.", "errors": errors}
    if isinstance(exc, ApiError):
        return {"message": str(exc.detail), "errors": exc.errors}
    if code == ErrorCode.AUTHENTICATION_FAILED:
        return {"message": _AUTH_FAILED_MESSAGE, "errors": {}}
    return {"message": str(getattr(exc, "detail", exc)), "errors": {}}


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        return internal_error_response()

    code = _code_for(exc)
    response.data = {"success": False, "code": code, **_error_body(exc, code)}
    return response


def internal_error_response() -> Response:
    return Response(
        {
            "success": False,
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "An unexpected error occurred.",
            "errors": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
