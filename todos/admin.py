from django.contrib import admin

from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("order", "target", "status", "created_at", "read_at", "done_at")
    list_filter = ("status", "target")
    search_fields = ("order__customer_name", "source_post__body")
