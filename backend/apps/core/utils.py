from dataclasses import dataclass

from rest_framework.settings import api_settings

USER_AGENT_MAX_LENGTH = 255


@dataclass(frozen=True)
class RequestMeta:
    """Minimal, privacy-conscious request context for audit records."""

    ip_address: str | None = None
    user_agent: str = ""


def get_client_ip(request) -> str | None:
    """Client IP, trusting X-Forwarded-For only for the configured number of proxies."""
    proxies = api_settings.NUM_PROXIES or 0
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if proxies and forwarded:
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
        if len(hops) >= proxies:
            return hops[-proxies]
    return request.META.get("REMOTE_ADDR") or None


def request_meta(request) -> RequestMeta:
    agent = request.META.get("HTTP_USER_AGENT", "")[:USER_AGENT_MAX_LENGTH]
    return RequestMeta(ip_address=get_client_ip(request), user_agent=agent)
