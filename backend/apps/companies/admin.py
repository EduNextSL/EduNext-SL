from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "work_email", "verification_status", "created_at")
    list_filter = ("verification_status",)
    search_fields = ("name", "work_email", "owner__email")
    readonly_fields = ("owner", "created_at", "updated_at")
