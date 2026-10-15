"""Business logic for registration, login and password reset. Views stay thin."""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.http import urlsafe_base64_decode

from apps.companies.models import Company
from apps.core.audit import record_event
from apps.core.exceptions import ApiError, ErrorCode
from apps.core.models import AuditEvent
from apps.core.utils import RequestMeta

from .emails import send_password_reset_email
from .models import LegalAcceptance, StudentProfile, User, UserRole
from .tokens import TokenPair, issue_tokens, revoke_all_user_tokens
from .validators import normalize_email

logger = logging.getLogger(__name__)


class EmailAlreadyRegistered(ApiError):
    status_code = 409
    error_code = ErrorCode.EMAIL_ALREADY_REGISTERED
    default_detail = "An account with this email already exists."

    def __init__(self):
        super().__init__(self.default_detail, errors={"email": [self.default_detail]})


class InvalidCredentials(ApiError):
    status_code = 401
    error_code = ErrorCode.INVALID_CREDENTIALS
    default_detail = "Invalid email or password."

    def __init__(self):
        super().__init__(self.default_detail)


# --- Registration -----------------------------------------------------------


def _record_legal_acceptance(user: User, meta: RequestMeta) -> None:
    LegalAcceptance.objects.create(
        user=user,
        terms_version=settings.LEGAL_TERMS_VERSION,
        user_agreement_version=settings.LEGAL_USER_AGREEMENT_VERSION,
        privacy_policy_version=settings.LEGAL_PRIVACY_POLICY_VERSION,
        ip_address=meta.ip_address,
    )


def _register(*, email: str, password: str, role: str, meta: RequestMeta, create_profile) -> User:
    """Create user + profile + legal acceptance atomically; map duplicate emails to 409."""
    email = normalize_email(email)
    try:
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password, role=role)
            create_profile(user)
            _record_legal_acceptance(user, meta)
            record_event(AuditEvent.REGISTRATION, actor=user, meta=meta, metadata={"role": role})
    except IntegrityError:
        # A concurrent request may have won the unique-email race.
        if User.objects.filter(email=email).exists():
            raise EmailAlreadyRegistered from None
        raise
    return user


def register_student(
    *, first_name: str, last_name: str, email: str, password: str, meta: RequestMeta
) -> User:
    return _register(
        email=email,
        password=password,
        role=UserRole.STUDENT,
        meta=meta,
        create_profile=lambda user: StudentProfile.objects.create(
            user=user, first_name=first_name, last_name=last_name
        ),
    )


def register_company(
    *,
    company_name: str,
    contact_full_name: str,
    work_email: str,
    password: str,
    meta: RequestMeta,
) -> User:
    return _register(
        email=work_email,
        password=password,
        role=UserRole.EMPLOYER,
        meta=meta,
        create_profile=lambda user: Company.objects.create(
            owner=user,
            name=company_name,
            contact_full_name=contact_full_name,
            work_email=user.email,
        ),
    )


# --- Login ------------------------------------------------------------------


@dataclass(frozen=True)
class LoginResult:
    user: User
    tokens: TokenPair


def login(
    *, request, email: str, password: str, remember_me: bool, meta: RequestMeta
) -> LoginResult:
    user = authenticate(request, email=normalize_email(email), password=password)
    if user is None:
        # No attempted email is stored: users sometimes type passwords into that field.
        record_event(AuditEvent.LOGIN_FAILURE, meta=meta)
        raise InvalidCredentials
    update_last_login(None, user)
    record_event(
        AuditEvent.LOGIN_SUCCESS, actor=user, meta=meta, metadata={"remember_me": remember_me}
    )
    return LoginResult(user=user, tokens=issue_tokens(user, remember_me=remember_me))


# --- Password reset ---------------------------------------------------------


def request_password_reset(*, email: str, meta: RequestMeta) -> None:
    """Send a reset email if the account exists. Never signals whether it did."""
    user = User.objects.filter(email=normalize_email(email)).first()
    record_event(
        AuditEvent.PASSWORD_RESET_REQUESTED,
        actor=user,
        meta=meta,
        metadata={"account_found": user is not None},
    )
    if user is None or not user.can_authenticate:
        return
    try:
        send_password_reset_email(user)
    except Exception as exc:  # delivery problems must not leak through the response
        logger.error("Password reset email delivery failed: %s", type(exc).__name__)


def resolve_reset_user(uid: str, token: str) -> User | None:
    """Return the user for a valid, unexpired, unused reset link; otherwise None."""
    try:
        pk = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=pk)
    except (
        TypeError,
        ValueError,
        OverflowError,
        UnicodeDecodeError,
        DjangoValidationError,
        User.DoesNotExist,
    ):
        return None
    if not user.can_authenticate or not default_token_generator.check_token(user, token):
        return None
    return user


@transaction.atomic
def complete_password_reset(*, user: User, new_password: str, meta: RequestMeta) -> None:
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    revoke_all_user_tokens(user)
    record_event(AuditEvent.PASSWORD_RESET_COMPLETED, actor=user, meta=meta)
