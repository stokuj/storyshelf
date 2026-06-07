from django.db import transaction

from .ai import MAX_CHARACTERS
from .models import Character, CharacterRelation, unique_character_slug
from .relations import RelationType

NAME_MAX = 200  # Character.name CharField length


def _clean_str(value) -> str:
    """LLM fields may be any JSON scalar; coerce non-strings to '' (skip), never raise."""
    return value.strip() if isinstance(value, str) else ""


def _as_list(value) -> list:
    """LLM may emit a non-list for characters/relations; treat anything else as empty."""
    return value if isinstance(value, list) else []


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
    for order, item in enumerate(_as_list(data.get("characters"))[:MAX_CHARACTERS]):
        if not isinstance(item, dict):
            continue
        name = _clean_str(item.get("name"))[:NAME_MAX]
        if not name:
            continue
        character = Character.objects.create(
            book=book,
            name=name,
            slug=unique_character_slug(book, name),
            role=_clean_str(item.get("role"))[:120],
            description=_clean_str(item.get("description")),
            order=order,
        )
        by_name[name] = character

    valid_types = set(RelationType.values)
    seen: set[tuple] = set()
    for rel in _as_list(data.get("relations")):
        if not isinstance(rel, dict):
            continue
        source = by_name.get(_clean_str(rel.get("from")))
        target = by_name.get(_clean_str(rel.get("to")))
        raw_type = _clean_str(rel.get("type")).lower().replace("-", "_")
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
