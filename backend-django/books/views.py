from django.db import models
from django.db.models import Prefetch, Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Chapter
from analysis.models import BookCharacter, CharacterRelationship
from .serializers import (
    BookListSerializer,
    BookDetailSerializer,
    ChapterSerializer,
    BookCharacterSerializer,
    CharacterRelationSerializer,
)


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


class ChapterView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        chapters = Chapter.objects.filter(book_id=book_id).order_by("chapter_number")
        return Response(ChapterSerializer(chapters, many=True).data)


class BookCharactersView(generics.ListAPIView):
    serializer_class = BookCharacterSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        book_id = self.kwargs.get("book_id")
        return BookCharacter.objects.filter(
            models.Q(relations_from__book_id=book_id) | models.Q(relations_to__book_id=book_id)
        ).distinct()


class BookRelationsView(generics.ListAPIView):
    serializer_class = CharacterRelationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return CharacterRelationship.objects.filter(book_id=self.kwargs["book_id"]).select_related(
            "from_character", "to_character"
        )
