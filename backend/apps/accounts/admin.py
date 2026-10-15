from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from apps.core.audit import record_event
from apps.core.models import AuditEvent
from apps.core.utils import request_meta

from .models import LegalAcceptance, StudentProfile, User


class UserCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "role", "status")


class UserChangeAdminForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserChangeAdminForm
    add_form = UserCreationForm
    ordering = ("-created_at",)
    list_display = ("email", "role", "status", "is_active", "created_at", "last_login")
    list_filter = ("role", "status", "is_active", "is_staff")
    search_fields = ("email",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Account", {"fields": ("role", "status", "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "status", "usable_password", "password1", "password2"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            return
        for field, event in (
            ("status", AuditEvent.ACCOUNT_STATUS_CHANGED),
            ("role", AuditEvent.ACCOUNT_ROLE_CHANGED),
        ):
            if field in form.changed_data:
                record_event(
                    event,
                    actor=request.user,
                    meta=request_meta(request),
                    metadata={
                        "target_user": str(obj.pk),
                        "from": form.initial.get(field),
                        "to": getattr(obj, field),
                    },
                )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "user", "created_at")
    search_fields = ("first_name", "last_name", "user__email")
    readonly_fields = ("user", "created_at", "updated_at")


@admin.register(LegalAcceptance)
class LegalAcceptanceAdmin(admin.ModelAdmin):
    """Read-only evidence of what each user accepted."""

    list_display = ("user", "terms_version", "privacy_policy_version", "accepted_at")
    search_fields = ("user__email",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
