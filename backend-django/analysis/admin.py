from django.contrib import admin, messages

from analysis.models import (
    BookCharacter,
    BookPlace,
    BookOrganization,
    CharacterRelationship,
)
from analysis.tasks import analyse_chapter, ner_chapter


@admin.register(BookCharacter)
class BookCharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(BookPlace)
class BookPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(BookOrganization)
class BookOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_character", "relation_type", "to_character", "book")
    list_filter = ("relation_type", "book")
    search_fields = ("from_character__name", "to_character__name")


@admin.action(description="Analyze selected books (all chapters)")
def analyze_selected_books(modeladmin, request, queryset):
    books_triggered = 0
    for book in queryset:
        if not book.chapters.exists():
            continue
        book.ner_completed_count = 0
        book.save()
        for chapter in book.chapters.all():
            if chapter.text:
                analyse_chapter.delay(chapter.id, chapter.text)
                ner_chapter.delay(chapter.id, chapter.text)
        books_triggered += 1
    messages.success(request, f"Analysis dispatched for {books_triggered} books.")
