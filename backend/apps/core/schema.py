"""OpenAPI helpers that describe the shared response envelopes."""

from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers

_envelope_cache: dict[str, type[serializers.Serializer]] = {}


class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    code = serializers.CharField(help_text="Stable machine-readable error code.")
    message = serializers.CharField()
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Field name -> list of messages. Empty for non-validation errors.",
    )


def envelope(name: str, data: type[serializers.Serializer] | None = None):
    """Build (once) a serializer class for {success, message?, data}."""
    if name not in _envelope_cache:
        attrs = {
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(required=False),
        }
        if data is not None:
            attrs["data"] = data()
        _envelope_cache[name] = type(name, (serializers.Serializer,), attrs)
    return _envelope_cache[name]


def error(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=ErrorResponseSerializer, description=description)
