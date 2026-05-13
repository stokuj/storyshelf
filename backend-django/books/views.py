from django.db.models import Prefetch, Q
from rest_framework import generics, permissions

from .models import Book, Chapter
from analysis.models import CharacterRelationship
from .serializers import BookListSerializer, BookDetailSerializer


class BookListView(generics.ListAPIView):
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
            Prefetch("reviews"),
            "authors",
            "tags",
            "genres",
        )
