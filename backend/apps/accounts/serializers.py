from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from apps.companies.models import Company

from .models import StudentProfile, User, UserRole
from .services import EmailAlreadyRegistered, resolve_reset_user
from .validators import normalize_email


class NormalizedEmailField(serializers.EmailField):
    """Valid email, trimmed and lower-cased."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return normalize_email(super().to_internal_value(data))


def _password_field(**kwargs) -> serializers.CharField:
    return serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
        max_length=128,
        **kwargs,
    )


def check_password_strength(password: str, *, email: str = ""):
    """Run Django's validators; the email feeds the similarity check."""
    try:
        validate_password(password, user=User(email=email))
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from None


# --- Registration -----------------------------------------------------------


class _RegistrationSerializer(serializers.Serializer):
    password = _password_field()
    password_confirm = _password_field()
    terms_accepted = serializers.BooleanField(
        help_text="Must be true: accepts Terms of Service, User Agreement and Privacy Policy."
    )

    email_field = "email"

    def validate_terms_accepted(self, value: bool) -> bool:
        if value is not True:
            raise serializers.ValidationError(
                "You must accept the Terms of Service, User Agreement and Privacy Policy."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": ["Passwords do not match."]})
        check_password_strength(attrs["password"], email=attrs.get(self.email_field, ""))
        return attrs

    def validate_email_unique(self, email: str) -> str:
        if User.objects.filter(email=email).exists():
            raise EmailAlreadyRegistered
        return email


class StudentRegistrationSerializer(_RegistrationSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = NormalizedEmailField()

    def validate_email(self, value):
        return self.validate_email_unique(value)


class CompanyRegistrationSerializer(_RegistrationSerializer):
    company_name = serializers.CharField(max_length=255)
    contact_full_name = serializers.CharField(max_length=255)
    work_email = NormalizedEmailField()

    email_field = "work_email"

    def validate_work_email(self, value):
        return self.validate_email_unique(value)


# --- Login / tokens ---------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=254)
    password = _password_field()
    remember_me = serializers.BooleanField(default=False)


class SocialLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(
        max_length=4096, help_text="Provider ID token (Google `credential`)."
    )
    terms_accepted = serializers.BooleanField(
        default=False, help_text="Required only when this sign-in creates a new account."
    )
    remember_me = serializers.BooleanField(default=False)


class ProviderConfigSerializer(serializers.Serializer):
    client_id = serializers.CharField()


class ProvidersSerializer(serializers.Serializer):
    google = ProviderConfigSerializer(allow_null=True)
    facebook = ProviderConfigSerializer(allow_null=True)


# --- Password reset ---------------------------------------------------------


class PasswordResetRequestSerializer(serializers.Serializer):
    email = NormalizedEmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=128)
    new_password = _password_field()
    new_password_confirm = _password_field()

    def validate(self, attrs):
        user = resolve_reset_user(attrs["uid"], attrs["token"])
        if user is None:
            # Deliberately one generic error for malformed, expired, used or foreign links.
            raise serializers.ValidationError(
                {"token": ["This reset link is invalid or has expired."]}
            )
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)}) from None
        attrs["user"] = user
        return attrs


# --- Output -----------------------------------------------------------------


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["first_name", "last_name"]


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "contact_full_name", "work_email", "verification_status"]


_PROFILE_SCHEMA = PolymorphicProxySerializer(
    component_name="Profile",
    serializers=[StudentProfileSerializer, CompanyProfileSerializer],
    resource_type_field_name=None,
)


class UserSerializer(serializers.ModelSerializer):
    """Safe public view of the authenticated account. Never add secrets or audit fields."""

    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "role", "status", "profile"]
        read_only_fields = fields

    @extend_schema_field(_PROFILE_SCHEMA)
    def get_profile(self, user: User):
        if user.role == UserRole.STUDENT:
            profile, serializer = getattr(user, "student_profile", None), StudentProfileSerializer
        elif user.role == UserRole.EMPLOYER:
            profile, serializer = getattr(user, "company", None), CompanyProfileSerializer
        else:
            return None
        return serializer(profile).data if profile else None


class SessionSerializer(serializers.Serializer):
    """Login/refresh payload. The refresh token is NOT here: it is an HttpOnly cookie."""

    access = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")
    access_expires_in = serializers.IntegerField(
        help_text="Seconds until the access token expires."
    )
    user = UserSerializer()


class RefreshedSessionSerializer(serializers.Serializer):
    access = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")
    access_expires_in = serializers.IntegerField()


class RegisteredUserSerializer(serializers.Serializer):
    user = UserSerializer()
