from typing import Any

from .models import AuditEvent, AuditLog
from .utils import RequestMeta


def record_event(
    event_type: AuditEvent,
    *,
    actor=None,
    meta: RequestMeta | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Persist an audit record. Callers must never put passwords, tokens or raw emails in metadata."""
    meta = meta or RequestMeta()
    return AuditLog.objects.create(
        event_type=event_type,
        actor=actor,
        ip_address=meta.ip_address,
        user_agent=meta.user_agent,
        metadata=metadata or {},
    )
