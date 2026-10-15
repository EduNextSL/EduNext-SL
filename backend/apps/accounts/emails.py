from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.email import get_email_sender

from .models import User


def build_password_reset_url(user: User) -> str:
    query = urlencode(
        {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        }
    )
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    return f"{base}{settings.FRONTEND_PASSWORD_RESET_PATH}?{query}"


def send_password_reset_email(user: User) -> None:
    minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    body = (
        "We received a request to reset your EduNext SL password.\n\n"
        f"Use this link to choose a new password (valid for {minutes} minutes, one use):\n"
        f"{build_password_reset_url(user)}\n\n"
        "If you did not request this, you can ignore this email; your password is unchanged."
    )
    get_email_sender().send(to=user.email, subject="Reset your EduNext SL password", body=body)
