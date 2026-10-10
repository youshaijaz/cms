from django.contrib import admin

from .models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "industry", "tone", "created_at")
    list_filter = ("tone", "created_at")
    search_fields = ("name", "industry", "owner__username")