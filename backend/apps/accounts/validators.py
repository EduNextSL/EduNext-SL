def normalize_email(value: str) -> str:
    """Canonical stored form of an email: trimmed and lower-cased.

    Used on every write and every lookup so uniqueness is case-insensitive.
    """
    return value.strip().lower()
