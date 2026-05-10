from django.contrib import admin
from .models import (
    Book,
    Chapter,
    StoryCharacter,
    BookCharacter,
    CharacterRelation,
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


class BookCharacterInline(admin.TabularInline):
    model = BookCharacter
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "rating", "ratings_count", "chapters_count")
    search_fields = ("title", "bookauthor__author__name", "genres")
    inlines = [ChapterInline, BookAuthorInline, BookCharacterInline]


@admin.register(StoryCharacter)
class StoryCharacterAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CharacterRelation)
class CharacterRelationAdmin(admin.ModelAdmin):
    list_display = ("book", "source", "target", "relation", "confidence")
    list_filter = ("book",)
