from datetime import date
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.email import deliver_email

from .models import User, UserRole


def build_password_reset_url(user: User) -> str:
    query = urlencode(
        {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        }
    )
    return f"{_frontend_url(settings.FRONTEND_PASSWORD_RESET_PATH)}?{query}"


def _frontend_url(path: str = "") -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}{path}"


def _render(template: str, context: dict) -> tuple[str, str]:
    """Render the branded HTML and plain-text versions of an email."""
    base = {
        "site_name": settings.SITE_NAME,
        "logo_url": settings.EMAIL_LOGO_URL,
        "support_email": settings.EMAIL_FROM_ADDRESS,
        "year": date.today().year,
    }
    context = {**base, **context}
    return (
        render_to_string(f"emails/{template}.txt", context),
        render_to_string(f"emails/{template}.html", context),
    )


def send_password_reset_email(user: User) -> None:
    text, html = _render(
        "password_reset",
        {
            "action_url": build_password_reset_url(user),
            "expires_minutes": settings.PASSWORD_RESET_TIMEOUT // 60,
        },
    )
    deliver_email(
        to=user.email,
        subject=f"Reset your {settings.SITE_NAME} password",
        body=text,
        html=html,
    )


def send_welcome_email(user: User) -> None:
    company = getattr(user, "company", None) if user.role == UserRole.EMPLOYER else None
    student = getattr(user, "student_profile", None) if user.role == UserRole.STUDENT else None
    name = (
        company.contact_full_name
        if company
        else (student.first_name if student else user.email.split("@")[0])
    )
    text, html = _render(
        "welcome",
        {
            "name": name,
            "email": user.email,
            "is_company": company is not None,
            "company_name": company.name if company else "",
            "action_url": _frontend_url("/login"),
        },
    )
    deliver_email(
        to=user.email,
        subject=f"Welcome to {settings.SITE_NAME}",
        body=text,
        html=html,
    )
