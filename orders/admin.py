from django.contrib import admin

from .models import CustomerTemplateItem, ImageTemplate, ImageTemplateItem, StatusOption, WorkOrder, WorkOrderImage


class CustomerTemplateItemInline(admin.TabularInline):
    model = CustomerTemplateItem
    extra = 0


class ImageTemplateItemInline(admin.TabularInline):
    model = ImageTemplateItem
    extra = 0


@admin.register(ImageTemplate)
class ImageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    inlines = [CustomerTemplateItemInline, ImageTemplateItemInline]


@admin.register(StatusOption)
class StatusOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active")
    list_filter = ("is_active",)


class WorkOrderImageInline(admin.TabularInline):
    model = WorkOrderImage
    extra = 0


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_display", "status", "creator", "updated_at")
    list_filter = ("status",)
    search_fields = ("customer_name", "customer_contact")
    inlines = [WorkOrderImageInline]
