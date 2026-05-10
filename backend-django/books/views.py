from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Chapter, BookAuthor, BookCharacter, CharacterRelation
from library.models import Author, Tag
from analysis.tasks import analyse_chapter, ner_chapter
from .serializers import (
    BookSerializer,
    BookCreateSerializer,
    BookDetailSerializer,
    ChapterSerializer,
    BookCharacterSerializer,
    CharacterRelationSerializer,
)


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "MODERATOR",
            "ADMIN",
        )


class BookListCreateView(generics.ListCreateAPIView):
    pagination_class = None  # flat list — frontend expects plain array

    def get_serializer_class(self):
        return BookCreateSerializer if self.request.method == "POST" else BookSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsModerator()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags")
        q = self.request.query_params.get("q", "")
        if q:
            q_lower = q.lower()
            qs = qs.filter(
                Q(title__icontains=q_lower)
                | Q(bookauthor__author__name__icontains=q_lower)
                | Q(genres__icontains=q_lower)
            ).distinct()
        return qs

    def perform_create(self, serializer):
        author_id = serializer.validated_data.pop("author_id")
        tags_list = serializer.validated_data.pop("tags", [])
        author = get_object_or_404(Author, id=author_id)
        book = serializer.save()
        BookAuthor.objects.create(book=book, author=author)
        for tag_name in tags_list:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            book.tags.add(tag)


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        return BookDetailSerializer if self.request.method == "GET" else BookSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsModerator()]

    def get_queryset(self):
        return Book.objects.prefetch_related(
            Prefetch("chapters", queryset=Chapter.objects.order_by("chapter_number")),
            Prefetch(
                "bookcharacter_set",
                queryset=BookCharacter.objects.select_related("character"),
            ),
            Prefetch(
                "character_relations",
                queryset=CharacterRelation.objects.select_related("source", "target"),
            ),
            Prefetch("reviews"),
            "authors",
            "tags",
        )


class ChapterView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsModerator()]

    def get(self, request, book_id):
        chapters = Chapter.objects.filter(book_id=book_id).order_by("chapter_number")
        return Response(ChapterSerializer(chapters, many=True).data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        text = uploaded_file.read().decode("utf-8")
        raw_chapters = [c.strip() for c in text.split("\n\n") if c.strip()]
        chapters_created = 0

        for i, content in enumerate(raw_chapters):
            chapter_num = i + 1
            title = content.split("\n")[0][:150] if "\n" in content else content[:150]
            chapter = Chapter.objects.create(
                book=book, chapter_number=chapter_num, title=title, content=content
            )
            chapters_created += 1

            analyse_chapter.delay(chapter.id, content)
            if chapter_num == 1:
                ner_chapter.delay(chapter.id, content)

        book.chapters_count = chapters_created
        book.save()
        return Response(
            {"bookId": book.id, "chaptersCreated": chapters_created},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        book.chapters.all().delete()
        book.chapters_count = 0
        book.ner_completed_count = 0
        book.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookCharactersView(generics.ListAPIView):
    serializer_class = BookCharacterSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return BookCharacter.objects.filter(
            book_id=self.kwargs["book_id"]
        ).select_related("character")


class BookRelationsView(generics.ListAPIView):
    serializer_class = CharacterRelationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return CharacterRelation.objects.filter(
            book_id=self.kwargs["book_id"]
        ).select_related("source", "target")
