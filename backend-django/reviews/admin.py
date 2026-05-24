from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "content_preview", "created_at")
    list_filter = ("rating",)
    search_fields = ("book__title", "user__handle")

    @admin.display(description="Content")
    def content_preview(self, obj):
        return obj.content[:100]
