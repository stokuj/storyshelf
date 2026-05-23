from django.contrib import admin

from .models import Shelf, ShelfEntry, ShelfMembership


class ShelfMembershipInline(admin.TabularInline):
    model = ShelfMembership
    extra = 0
    readonly_fields = ("added_at",)
    raw_id_fields = ("book",)


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "slug", "is_public", "book_count", "created_at")
    list_filter = ("is_public",)
    search_fields = ("name", "user__username")
    readonly_fields = ("slug", "created_at", "updated_at")
    inlines = [ShelfMembershipInline]

    def book_count(self, obj):
        return obj.memberships.count()

    book_count.short_description = "Books"
