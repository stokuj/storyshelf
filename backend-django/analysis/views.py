from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import BookCharacter, CharacterRelationship
from .serializers import AIExtractionSerializer, BookCharacterSerializer, MergeRequestSerializer
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


class BookCharacterMergeView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, book_id, character_id):
        source = get_object_or_404(BookCharacter, pk=character_id, book_id=book_id)
        serializer = MergeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_id = serializer.validated_data["into"]

        if target_id == source.pk:
            return Response(
                {"detail": "Cannot merge a character into itself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target = BookCharacter.objects.get(pk=target_id)
        except BookCharacter.DoesNotExist:
            return Response({"detail": "Target character not found."}, status=status.HTTP_404_NOT_FOUND)

        if target.book_id != source.book_id:
            return Response(
                {"detail": "Target character must belong to the same book."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if source.canonical_id is not None:
            return Response(
                {"detail": "Source is already an alias; merge its canonical instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target.canonical_id is not None:
            return Response(
                {"detail": "Target is an alias; provide the canonical id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        _perform_merge(source, target)
        target.refresh_from_db()
        return Response(BookCharacterSerializer(target).data)


def _perform_merge(source, target):
    with transaction.atomic():
        # 1. Re-point any aliases of source to target
        source.aliases.all().update(canonical=target)

        # 2. Build set of existing (from_id, to_id) pairs NOT involving source
        existing = set(
            CharacterRelationship.objects.filter(book=source.book)
            .exclude(Q(from_character=source) | Q(to_character=source))
            .values_list("from_character_id", "to_character_id")
        )

        # 3. Re-point source's relations to target, deduplicating
        for rel in CharacterRelationship.objects.filter(
            Q(from_character=source) | Q(to_character=source)
        ):
            new_from = target.pk if rel.from_character_id == source.pk else rel.from_character_id
            new_to = target.pk if rel.to_character_id == source.pk else rel.to_character_id

            if new_from == new_to:  # self-relation created by merge
                rel.delete()
                continue

            key = (new_from, new_to)
            if key in existing:
                rel.delete()
            else:
                existing.add(key)
                rel.from_character_id = new_from
                rel.to_character_id = new_to
                rel.save(update_fields=["from_character_id", "to_character_id"])

        # 4. Accumulate mention_count
        BookCharacter.objects.filter(pk=target.pk).update(
            mention_count=F("mention_count") + source.mention_count
        )

        # 5. Mark source as alias
        source.canonical = target
        source.is_hidden = True
        source.save(update_fields=["canonical_id", "is_hidden"])
