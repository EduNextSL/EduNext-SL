from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import record_event
from apps.core.exceptions import ApiError, ErrorCode
from apps.core.models import AuditEvent
from apps.core.permissions import TrustedOriginMixin
from apps.core.responses import success_response
from apps.core.schema import envelope, error
from apps.core.throttling import (
    LoginIdentityThrottle,
    LoginThrottle,
    PasswordResetConfirmThrottle,
    PasswordResetRequestThrottle,
    RegistrationThrottle,
    SocialLoginThrottle,
    TokenRefreshThrottle,
)
from apps.core.utils import request_meta

from . import services, social, tokens
from .cookies import clear_refresh_cookie, read_refresh_cookie, set_refresh_cookie
from .serializers import (
    CompanyRegistrationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshedSessionSerializer,
    RegisteredUserSerializer,
    SessionSerializer,
    StudentRegistrationSerializer,
    UserSerializer,
)

GENERIC_RESET_MESSAGE = "If an account exists for that email, a password reset link has been sent."

MessageResponse = envelope("MessageResponse")
RegisteredResponse = envelope("RegisteredResponse", RegisteredUserSerializer)
SessionResponse = envelope("SessionResponse", SessionSerializer)
RefreshedResponse = envelope("RefreshedResponse", RefreshedSessionSerializer)
MeResponse = envelope("MeResponse", RegisteredUserSerializer)

VALIDATION_ERROR = error("Validation failed (`VALIDATION_ERROR`).")
THROTTLED = error("Too many requests (`THROTTLED`); see the `Retry-After` header.")


class PublicAPIView(APIView):
    """Unauthenticated endpoint: ignores any Authorization header and allows anyone."""

    authentication_classes: list = []
    permission_classes = [AllowAny]


def _session_payload(pair: tokens.TokenPair) -> dict:
    return {
        "access": pair.access,
        "token_type": "Bearer",
        "access_expires_in": pair.access_expires_in,
    }


class StudentRegisterView(PublicAPIView):
    throttle_classes = [RegistrationThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Register a student account",
        request=StudentRegistrationSerializer,
        responses={
            201: RegisteredResponse,
            400: VALIDATION_ERROR,
            409: error("Email already registered (`EMAIL_ALREADY_REGISTERED`)."),
            429: THROTTLED,
        },
    )
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = services.register_student(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data["password"],
            meta=request_meta(request),
        )
        return success_response(
            {"user": UserSerializer(user).data},
            message="Account created.",
            status=status.HTTP_201_CREATED,
        )


class CompanyRegisterView(PublicAPIView):
    throttle_classes = [RegistrationThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Register a company (employer) account",
        request=CompanyRegistrationSerializer,
        responses={
            201: RegisteredResponse,
            400: VALIDATION_ERROR,
            409: error("Email already registered (`EMAIL_ALREADY_REGISTERED`)."),
            429: THROTTLED,
        },
    )
    def post(self, request):
        serializer = CompanyRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = services.register_company(
            company_name=data["company_name"],
            contact_full_name=data["contact_full_name"],
            work_email=data["work_email"],
            password=data["password"],
            meta=request_meta(request),
        )
        return success_response(
            {"user": UserSerializer(user).data},
            message="Account created.",
            status=status.HTTP_201_CREATED,
        )


class LoginView(TrustedOriginMixin, PublicAPIView):
    throttle_classes = [LoginThrottle, LoginIdentityThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Log in with email and password",
        description=(
            "Returns a short-lived access token in the body and sets the refresh token as an "
            "HttpOnly cookie. Wrong password, unknown email, and suspended/disabled accounts all "
            "return the same 401."
        ),
        request=LoginSerializer,
        responses={
            200: SessionResponse,
            400: VALIDATION_ERROR,
            401: error("Invalid credentials (`INVALID_CREDENTIALS`)."),
            403: error("Origin not allowed (`PERMISSION_DENIED`)."),
            429: THROTTLED,
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.login(
            request=request,
            email=data["email"],
            password=data["password"],
            remember_me=data["remember_me"],
            meta=request_meta(request),
        )
        response = success_response(
            {**_session_payload(result.tokens), "user": UserSerializer(result.user).data}
        )
        set_refresh_cookie(response, result.tokens)
        return response


class RefreshView(TrustedOriginMixin, PublicAPIView):
    throttle_classes = [TokenRefreshThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Rotate the refresh cookie and get a new access token",
        description=(
            "Reads the refresh token from the HttpOnly cookie (no body). Each refresh token is "
            "single-use; reusing one revokes every session of that user. Issue one refresh at a time."
        ),
        request=None,
        responses={
            200: RefreshedResponse,
            401: error("Missing/invalid/revoked/expired refresh token (`INVALID_REFRESH_TOKEN`)."),
            403: error("Origin not allowed (`PERMISSION_DENIED`)."),
            429: THROTTLED,
        },
    )
    def post(self, request):
        raw = read_refresh_cookie(request)
        if raw is None:
            return _refresh_failure_response()
        try:
            pair = tokens.rotate_refresh_token(raw, request_meta(request))
        except tokens.InvalidRefreshToken:
            return _refresh_failure_response()
        response = success_response(_session_payload(pair))
        set_refresh_cookie(response, pair)
        return response


def _refresh_failure_response() -> Response:
    response = Response(
        {
            "success": False,
            "code": ErrorCode.INVALID_REFRESH_TOKEN,
            "message": tokens.InvalidRefreshToken.default_detail,
            "errors": {},
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )
    clear_refresh_cookie(response)
    return response


class LogoutView(TrustedOriginMixin, PublicAPIView):
    """Idempotent: always clears the cookie and revokes the refresh token if one is valid."""

    throttle_classes = [TokenRefreshThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Log out (revoke the refresh token)",
        request=None,
        responses={
            204: OpenApiResponse(description="Refresh token revoked and cookie cleared."),
            403: error("Origin not allowed (`PERMISSION_DENIED`)."),
            429: THROTTLED,
        },
    )
    def post(self, request):
        raw = read_refresh_cookie(request)
        user = tokens.revoke_refresh_token(raw) if raw else None
        if user is not None:
            record_event(AuditEvent.LOGOUT, actor=user, meta=request_meta(request))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    """Always resolves the account from the access token; accepts no user identifier."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        summary="Current authenticated user",
        responses={
            200: MeResponse,
            401: error("Missing, invalid or expired access token (`NOT_AUTHENTICATED`)."),
        },
    )
    def get(self, request):
        return success_response({"user": UserSerializer(request.user).data})


class PasswordResetRequestView(PublicAPIView):
    throttle_classes = [PasswordResetRequestThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Request a password reset email",
        description="Always returns the same 200 response, whether or not the email has an account.",
        request=PasswordResetRequestSerializer,
        responses={200: MessageResponse, 400: VALIDATION_ERROR, 429: THROTTLED},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(
            email=serializer.validated_data["email"], meta=request_meta(request)
        )
        return success_response(message=GENERIC_RESET_MESSAGE)


class PasswordResetConfirmView(PublicAPIView):
    throttle_classes = [PasswordResetConfirmThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Set a new password using an emailed link",
        description=(
            "`uid` and `token` come from the emailed link. Links expire and work once. "
            "On success all existing sessions are revoked."
        ),
        request=PasswordResetConfirmSerializer,
        responses={200: MessageResponse, 400: VALIDATION_ERROR, 429: THROTTLED},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.complete_password_reset(
            user=serializer.validated_data["user"],
            new_password=serializer.validated_data["new_password"],
            meta=request_meta(request),
        )
        return success_response(message="Password has been reset. You can now log in.")


class SocialLoginNotConfigured(ApiError):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    error_code = ErrorCode.NOT_IMPLEMENTED
    default_detail = "Social login is not available yet."

    def __init__(self):
        super().__init__(self.default_detail)


class SocialLoginView(PublicAPIView):
    """Placeholder endpoint for Google/Facebook; see apps/accounts/social.py."""

    throttle_classes = [SocialLoginThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Social login (not yet available)",
        description="Returns 501 until provider credentials and account-linking rules are configured.",
        request=None,
        responses={
            404: error("Unknown provider (`NOT_FOUND`)."),
            501: error("Provider not configured (`NOT_IMPLEMENTED`)."),
        },
    )
    def post(self, request, provider: str):
        if provider not in social.SocialProvider.ALL:
            raise NotFound
        # Once a verifier is registered, verify the credential and log the user in here.
        raise SocialLoginNotConfigured
