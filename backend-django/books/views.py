from django.db.models import Prefetch, Q
from rest_framework import generics, permissions

from analysis.models import CharacterRelationship

from .models import Book, Chapter
from .serializers import BookDetailSerializer, BookListSerializer


class BookListView(generics.ListAPIView):
    """
    Zwraca płaską listę wszystkich książek.
    Filtrowanie pełnotekstowe: ?q=<fraza> — przeszukuje tytuł, nazwisko autora i gatunek.
    """

    serializer_class = BookListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags", "genres")
        q = self.request.query_params.get("q", "")
        if q:
            q_lower = q.lower()
            qs = qs.filter(
                Q(title__icontains=q_lower)
                | Q(bookauthor__author__name__icontains=q_lower)
                | Q(genres__name__icontains=q_lower)
            ).distinct()
        return qs


class BookRetrieveView(generics.RetrieveAPIView):
    """
    Szczegóły książki wraz z rozdziałami (posortowanymi), relacjami między postaciami,
    autorami, tagami i gatunkami.
    """

    serializer_class = BookDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Book.objects.prefetch_related(
            Prefetch("chapters", queryset=Chapter.objects.order_by("chapter_number")),
            Prefetch(
                "character_relationships",
                queryset=CharacterRelationship.objects.select_related(
                    "from_character", "to_character"
                ),
            ),
            "authors",
            "tags",
            "genres",
        )
