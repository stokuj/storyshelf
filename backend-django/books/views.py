from django.db.models import Prefetch, Q
from rest_framework import generics, permissions
from rest_framework.response import Response

from shelf.models import ShelfEntry

from .lookups import resolve_book
from .models import Book
from .serializers import BookDetailSerializer, BookListSerializer

SORT_MAP = {
    "rating": ["-avg_rating", "-ratings_count"],
    "recent": ["-created_at", "-id"],
    "popular": ["-ratings_count", "-avg_rating"],
}
DEFAULT_ORDER = ["title"]


class BookListView(generics.ListAPIView):
    serializer_class = BookListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags", "genres")

        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(bookauthor__author__name__icontains=q)
                | Q(genres__name__icontains=q)
            ).distinct()

        genre = self.request.query_params.get("genre", "").strip()
        if genre:
            qs = qs.filter(genres__name__iexact=genre).distinct()

        sort = self.request.query_params.get("sort", "").strip()
        qs = qs.order_by(*SORT_MAP.get(sort, DEFAULT_ORDER))

        return qs

    def list(self, request, *args, **kwargs):
        if request.query_params.get("paginate") == "false":
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


class BookRetrieveView(generics.RetrieveAPIView):
    serializer_class = BookDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        from analysis.models import BookCharacter

        id_or_slug = self.kwargs.get("id_or_slug") or str(self.kwargs.get("pk", ""))
        is_admin = bool(self.request.user and self.request.user.is_staff)

        chars_qs = (
            BookCharacter.objects.all()
            if is_admin
            else BookCharacter.objects.filter(is_hidden=False, canonical__isnull=True)
        )

        qs = Book.objects.select_related("serie").prefetch_related(
            Prefetch("characters", queryset=chars_qs),
            "authors",
            "tags",
            "genres",
            "character_relationships__from_character",
            "character_relationships__to_character",
        )
        if self.request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    "shelf_entries",
                    queryset=ShelfEntry.objects.filter(user=self.request.user),
                    to_attr="current_user_shelf_entries",
                )
            )
        book = resolve_book(id_or_slug)
        return qs.get(pk=book.pk)


class BookContainsCharacterView(generics.ListAPIView):
    serializer_class = BookListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        name = self.request.query_params.get("name", "").strip()
        if not name:
            return Book.objects.none()
        return (
            Book.objects.filter(characters__name__icontains=name)
            .select_related("serie")
            .prefetch_related("authors", "genres", "tags")
            .distinct()
            .order_by("title")
        )
