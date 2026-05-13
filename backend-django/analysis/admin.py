from django.contrib import admin, messages

from analysis.models import (
    BookCharacter,
    BookOrganization,
    BookPlace,
    CharacterRelationship,
)
from analysis.tasks import analyse_book


@admin.register(BookCharacter)
class BookCharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(BookPlace)
class BookPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(BookOrganization)
class BookOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_character", "relation_type", "to_character", "book")
    list_filter = ("relation_type", "book")
    search_fields = ("from_character__name", "to_character__name")


@admin.action(description="Analyse selected books (NER + LLM)")
def analyze_selected_books(modeladmin, request, queryset):
    triggered = 0
    for book in queryset:
        if not book.text:
            continue
        analyse_book.delay(book.id)
        triggered += 1
    messages.success(request, f"Analysis dispatched for {triggered} books.")
