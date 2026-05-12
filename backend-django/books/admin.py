from django.contrib import admin
from .models import (
    Book,
    Chapter,
    BookAuthor,
    BookTag,
)


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("chapter_number", "title", "analysis_completed")


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "avg_rating", "ratings_count", "chapters_count")
    search_fields = ("title", "bookauthor__author__name", "genres")
    inlines = [ChapterInline, BookAuthorInline]
