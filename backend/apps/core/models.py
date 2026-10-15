import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.TextChoices):
    REGISTRATION = "registration", "Registration"
    LOGIN_SUCCESS = "login_success", "Login success"
    LOGIN_FAILURE = "login_failure", "Login failure"
    LOGOUT = "logout", "Logout"
    REFRESH_TOKEN_REUSE = "refresh_token_reuse", "Refresh token reuse detected"
    PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password reset requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed", "Password reset completed"
    ACCOUNT_STATUS_CHANGED = "account_status_changed", "Account status changed"
    ACCOUNT_ROLE_CHANGED = "account_role_changed", "Account role changed"


class AuditLog(models.Model):
    """Append-only record of security-relevant events. Never store secrets or raw emails here."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=AuditEvent.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
