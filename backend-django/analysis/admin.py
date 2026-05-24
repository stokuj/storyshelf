from django.contrib import admin, messages

from analysis.models import (
    BookCharacter,
    BookOrganization,
    BookPlace,
    CharacterRelationship,
)
from analysis.tasks import analyse_book


@admin.action(description="Mark selected characters as hidden")
def mark_hidden(modeladmin, request, queryset):
    updated = queryset.update(is_hidden=True)
    messages.success(request, f"{updated} character(s) marked as hidden.")


@admin.action(description="Mark selected characters as visible")
def mark_visible(modeladmin, request, queryset):
    updated = queryset.update(is_hidden=False)
    messages.success(request, f"{updated} character(s) marked as visible.")


def unmerge_aliases(modeladmin, request, queryset):
    aliases = queryset.filter(canonical__isnull=False)
    count = aliases.update(canonical=None, is_hidden=False)
    modeladmin.message_user(
        request,
        f"{count} alias(es) unmerged. Note: relations and mention counts "
        "were NOT restored — fix manually if needed.",
        level="warning",
    )


unmerge_aliases.short_description = "Unmerge selected aliases (canonical → NULL, is_hidden → False)"


@admin.register(BookCharacter)
class BookCharacterAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "book", "mention_count", "source", "is_hidden", "confidence", "canonical"
    )
    search_fields = ("name", "slug")
    list_filter = ("book", "source", "is_hidden", ("canonical", admin.EmptyFieldListFilter))
    actions = [mark_hidden, mark_visible, unmerge_aliases]
    readonly_fields = ("slug",)
    raw_id_fields = ("canonical",)


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
