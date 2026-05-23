from django.shortcuts import get_object_or_404

from .models import Book


def resolve_book(id_or_slug: str) -> Book:
    """Resolve a Book by integer PK (if numeric) or by slug. Raises Http404 if not found."""
    if id_or_slug.isdigit():
        return get_object_or_404(Book, pk=int(id_or_slug))
    return get_object_or_404(Book, slug=id_or_slug)
