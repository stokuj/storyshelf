from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import Character, CharacterAnalysis
from .serializers import CharacterDetailSerializer, CharacterListResponseSerializer
from .tasks import generate_characters_task

_status_response = inline_serializer(
    name="CharacterAnalysisStatus", fields={"status": serializers.CharField()}
)


class GenerateCharactersView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "character_generate"

    @extend_schema(request=None, responses={202: _status_response})
    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        analysis, created = CharacterAnalysis.objects.get_or_create(book=book)
        active = analysis.status in (
            CharacterAnalysis.Status.PENDING,
            CharacterAnalysis.Status.RUNNING,
        )
        # Idempotent: a pre-existing PENDING/RUNNING analysis is left alone (one job
        # per book). Otherwise (just created, or previously done/failed) re-dispatch.
        if created or not active:
            analysis.status = CharacterAnalysis.Status.PENDING
            analysis.error_message = ""
            analysis.save(update_fields=["status", "error_message", "updated_at"])
            generate_characters_task.delay(book.id)
        return Response({"status": analysis.status}, status=status.HTTP_202_ACCEPTED)


class CharacterListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CharacterListResponseSerializer)
    def get(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        analysis = CharacterAnalysis.objects.filter(book=book).first()
        characters = Character.objects.filter(book=book)
        payload = {
            "status": analysis.status if analysis else None,
            "characters": characters,
        }
        return Response(CharacterListResponseSerializer(payload).data)


class CharacterDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CharacterDetailSerializer)
    def get(self, request, slug, char_slug):
        character = get_object_or_404(
            Character.objects.prefetch_related("relations_from__to_character"),
            book__slug=slug,
            slug=char_slug,
        )
        return Response(CharacterDetailSerializer(character).data)
