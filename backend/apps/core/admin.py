from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: audit records are append-only and written by the application."""

    list_display = ("created_at", "event_type", "actor", "ip_address")
    list_filter = ("event_type",)
    search_fields = ("actor__email", "ip_address")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
