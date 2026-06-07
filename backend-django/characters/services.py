from django.db import transaction

from .ai import MAX_CHARACTERS
from .models import Character, CharacterRelation, unique_character_slug
from .relations import RelationType


@transaction.atomic
def store_characters(book, data: dict) -> None:
    """Replace all characters + relations for `book` from validated LLM `data`.

    Delete-and-replace keeps regeneration simple. Relations whose endpoints are
    not among the stored characters are skipped (the LLM occasionally references
    names it did not include).
    """
    CharacterRelation.objects.filter(book=book).delete()
    Character.objects.filter(book=book).delete()

    by_name: dict[str, Character] = {}
    for order, item in enumerate(data.get("characters", [])[:MAX_CHARACTERS]):
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue
        character = Character.objects.create(
            book=book,
            name=name,
            slug=unique_character_slug(book, name),
            role=(item.get("role") or "").strip()[:120],
            description=(item.get("description") or "").strip(),
            order=order,
        )
        by_name[name] = character

    valid_types = set(RelationType.values)
    seen: set[tuple] = set()
    for rel in data.get("relations", []):
        if not isinstance(rel, dict):
            continue
        source = by_name.get((rel.get("from") or "").strip())
        target = by_name.get((rel.get("to") or "").strip())
        raw_type = (rel.get("type") or "").strip().lower()
        relation_type = raw_type if raw_type in valid_types else RelationType.OTHER
        key = (id(source), id(target), relation_type)
        if source and target and source != target and key not in seen:
            seen.add(key)
            CharacterRelation.objects.create(
                book=book,
                from_character=source,
                to_character=target,
                relation_type=relation_type,
            )
