"""Email abstraction: swap the sender via settings.EMAIL_SENDER_CLASS."""

from typing import Protocol

from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string


class EmailSender(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class DjangoEmailSender:
    """Delivers through whichever Django EMAIL_BACKEND is configured (see EMAIL_URL)."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)


def get_email_sender() -> EmailSender:
    return import_string(settings.EMAIL_SENDER_CLASS)()
