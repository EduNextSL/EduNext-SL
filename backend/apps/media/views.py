from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.exceptions import ApiError, ErrorCode
from apps.core.responses import success_response
from apps.core.schema import envelope, error
from apps.core.throttling import UploadSignatureThrottle

from .services import UPLOAD_POLICIES, MediaNotConfigured, build_upload_signature


class UploadSignatureRequestSerializer(serializers.Serializer):
    resource_type = serializers.ChoiceField(
        choices=sorted(UPLOAD_POLICIES), help_text="image, video, or raw (documents)."
    )


class UploadSignatureSerializer(serializers.Serializer):
    upload_url = serializers.URLField()
    api_key = serializers.CharField()
    signature = serializers.CharField()
    form_fields = serializers.DictField(help_text="Form fields to send unchanged with the file.")
    max_bytes = serializers.IntegerField()


class MediaNotAvailable(ApiError):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    error_code = ErrorCode.NOT_IMPLEMENTED
    default_detail = "File uploads are not configured."

    def __init__(self):
        super().__init__(self.default_detail)


class UploadSignatureView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UploadSignatureThrottle]

    @extend_schema(
        tags=["media"],
        summary="Get a signed Cloudinary upload",
        description=(
            "Returns parameters for a direct browser-to-Cloudinary upload: POST multipart form "
            "data to `upload_url` with `file`, `api_key`, `signature` and every entry of `form_fields`. "
            "The response of that upload contains the asset `secure_url`/`public_id`."
        ),
        request=UploadSignatureRequestSerializer,
        responses={
            200: envelope("UploadSignatureResponse", UploadSignatureSerializer),
            400: error("Validation failed (`VALIDATION_ERROR`)."),
            401: error("Not authenticated (`NOT_AUTHENTICATED`)."),
            501: error("Cloudinary not configured (`NOT_IMPLEMENTED`)."),
        },
    )
    def post(self, request):
        serializer = UploadSignatureRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = build_upload_signature(request.user, serializer.validated_data["resource_type"])
        except MediaNotConfigured:
            raise MediaNotAvailable from None
        return success_response(data)
