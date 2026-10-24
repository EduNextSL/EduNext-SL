"""Email abstraction: swap the sender via settings.EMAIL_SENDER_CLASS.

`deliver_email` is what application code calls. It never raises and, unless
settings.EMAIL_ASYNC is false, never blocks the request on the mail provider.
"""

import logging
import threading
from typing import Protocol

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_TIMEOUT_SECONDS = 10


class EmailDeliveryError(Exception):
    pass


class EmailSender(Protocol):
    def send(self, *, to: str, subject: str, body: str, html: str | None = None) -> None: ...


class DjangoEmailSender:
    """Delivers through whichever Django EMAIL_BACKEND is configured (see EMAIL_URL)."""

    def send(self, *, to, subject, body, html=None):
        message = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
        if html:
            message.attach_alternative(html, "text/html")
        message.send(fail_silently=False)


class BrevoEmailSender:
    """Sends through Brevo's transactional email HTTP API (BREVO_API_KEY)."""

    def send(self, *, to, subject, body, html=None):
        payload = {
            "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM_ADDRESS},
            "to": [{"email": to}],
            "subject": subject,
            "textContent": body,
        }
        if html:
            payload["htmlContent"] = html
        try:
            response = requests.post(
                BREVO_SEND_URL,
                json=payload,
                headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
                timeout=BREVO_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise EmailDeliveryError(f"Brevo unreachable ({type(exc).__name__})") from None
        if response.status_code >= 300:
            # Status and Brevo's error code only: never the payload (it holds the recipient).
            try:
                code = response.json().get("code", "")
            except ValueError:
                code = ""
            raise EmailDeliveryError(
                f"Brevo rejected the email (HTTP {response.status_code} {code})"
            )


def get_email_sender() -> EmailSender:
    return import_string(settings.EMAIL_SENDER_CLASS)()


def _deliver(to: str, subject: str, body: str, html: str | None) -> None:
    try:
        get_email_sender().send(to=to, subject=subject, body=body, html=html)
    except Exception as exc:  # delivery problems must never break the caller
        logger.error(
            "Email delivery failed: %s",
            exc if isinstance(exc, EmailDeliveryError) else type(exc).__name__,
        )


def deliver_email(*, to: str, subject: str, body: str, html: str | None = None) -> None:
    if settings.EMAIL_ASYNC:
        threading.Thread(target=_deliver, args=(to, subject, body, html), daemon=True).start()
    else:
        _deliver(to, subject, body, html)
