from django.contrib import admin

from analysis.admin import analyze_selected_books

from .models import (
    Book,
    BookAuthor,
    # TODO(task5): Chapter removed
    # Chapter,
)


# TODO(task5): ChapterInline removed
# class ChapterInline(admin.TabularInline):
#     model = Chapter
#     extra = 0
#     fields = ("chapter_number", "title", "analysis_completed")


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "avg_rating", "ratings_count")
    search_fields = ("title", "bookauthor__author__name", "genres")
    inlines = [BookAuthorInline]
    actions = [analyze_selected_books]


# TODO(task5): ChapterAdmin removed
# @admin.register(Chapter)
# class ChapterAdmin(admin.ModelAdmin):
#     list_display = ("chapter_number", "title", "book", "analysis_completed")
