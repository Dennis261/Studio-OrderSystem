from django.contrib import admin

from .models import Post, PostAttachment


class PostAttachmentInline(admin.TabularInline):
    model = PostAttachment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("order", "author", "created_at")
    search_fields = ("body", "order__customer_name")
    inlines = [PostAttachmentInline]
