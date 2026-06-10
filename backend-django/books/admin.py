from django.contrib import admin

from .models import Book, BookAuthor


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "avg_rating", "ratings_count")
    search_fields = ("title", "bookauthor__author__name")
    inlines = [BookAuthorInline]
    readonly_fields = ("avg_rating", "ratings_count")
    fields = (
        "title", "year", "isbn", "description", "page_count",
        "serie", "position_in_series",
        "avg_rating", "ratings_count",
    )
