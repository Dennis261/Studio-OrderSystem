from django.contrib import admin

from .models import ActivityLog, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name", "is_admin", "is_active")
    list_filter = ("is_admin", "is_active")
    search_fields = ("name",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_repr", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("actor__name", "target_repr", "summary")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "target_repr",
        "summary",
        "metadata",
        "ip_address",
        "user_agent",
        "created_at",
    )
