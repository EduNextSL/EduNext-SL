import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from .validators import normalize_email


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    EMPLOYER = "employer", "Employer"
    INSTRUCTOR = "instructor", "Instructor"
    MODERATOR = "moderator", "Moderator"
    ADMINISTRATOR = "administrator", "Administrator"


class AccountStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PENDING = "pending", "Pending"
    SUSPENDED = "suspended", "Suspended"
    DISABLED = "disabled", "Disabled"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email: str):
        return self.get(email=normalize_email(email))

    def create_user(self, email: str, password: str | None = None, **extra):
        if not email:
            raise ValueError("Email is required.")
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("role", UserRole.ADMINISTRATOR)
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Email-identified account. `role` and `status` are the server-side source of truth."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    status = models.CharField(
        max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]
        indexes = [models.Index(fields=["role", "status"])]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        super().save(*args, **kwargs)

    @property
    def can_authenticate(self) -> bool:
        """True only for enabled accounts in the active state."""
        return self.is_active and self.status == AccountStatus.ACTIVE


class StudentProfile(models.Model):
    """Profile for student accounts. Phone, education, bio, CV reference, etc. come later."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile"
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class LegalAcceptance(models.Model):
    """Auditable record that a user accepted specific legal document versions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="legal_acceptances"
    )
    terms_version = models.CharField(max_length=50)
    user_agreement_version = models.CharField(max_length=50)
    privacy_policy_version = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]
        indexes = [models.Index(fields=["user", "-accepted_at"])]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.accepted_at:%Y-%m-%d}"


class SocialAccount(models.Model):
    """Link between a user and an identity at an external provider (e.g. Google)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_accounts"
    )
    provider = models.CharField(max_length=20)
    subject = models.CharField(max_length=255, help_text="Provider's stable user id.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "subject"], name="accounts_socialaccount_identity_unique"
            ),
            models.UniqueConstraint(
                fields=["user", "provider"], name="accounts_socialaccount_user_provider_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.user_id}"
