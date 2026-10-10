from django.contrib import admin

from .models import Post, PostTemplate


@admin.register(PostTemplate)
class PostTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "layout", "is_active")
    list_filter = ("is_active",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("headline", "brand", "template", "created_at")
    list_filter = ("template", "created_at")
    search_fields = ("headline", "brand__name")
    readonly_fields = ("created_at",)