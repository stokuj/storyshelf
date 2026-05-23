from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import BookCharacter
from .serializers import AIExtractionSerializer, BookCharacterSerializer
from .tasks import analyse_book


class AIExtractionTriggerView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, book_id):
        book = get_object_or_404(
            Book.objects.prefetch_related("characters", "character_relationships"),
            pk=book_id,
        )
        if book.ai_extraction_status in ("pending", "running"):
            return Response(AIExtractionSerializer(book).data, status=status.HTTP_200_OK)

        Book.objects.filter(pk=book_id).update(
            ai_extraction_status="pending",
            ai_extraction_failure_reason="",
        )
        analyse_book.delay(book_id)

        book.refresh_from_db()
        return Response(AIExtractionSerializer(book).data, status=status.HTTP_202_ACCEPTED)


class AIExtractionRetrieveView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, book_id):
        book = get_object_or_404(
            Book.objects.prefetch_related("characters", "character_relationships"),
            pk=book_id,
        )
        return Response(AIExtractionSerializer(book).data)


class BookCharacterHideView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, book_id, character_id):
        char = get_object_or_404(BookCharacter, pk=character_id, book_id=book_id)
        hidden = bool(request.data.get("hidden", True))
        char.is_hidden = hidden
        char.save(update_fields=["is_hidden"])
        return Response(BookCharacterSerializer(char).data)
