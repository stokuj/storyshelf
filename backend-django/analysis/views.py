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
        char = get_object_or_404(BookCharacter.all_objects, pk=character_id, book_id=book_id)
        hidden = bool(request.data.get("hidden", True))
        char.is_hidden = hidden
        char.save(update_fields=["is_hidden"])
        return Response(BookCharacterSerializer(char).data)


class BookCharacterMergeView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, book_id, character_id):
        source = get_object_or_404(BookCharacter.all_objects, pk=character_id, book_id=book_id)
        serializer = MergeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_id = serializer.validated_data["into"]

        if target_id == source.pk:
            return Response(
                {"detail": "Cannot merge a character into itself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target = BookCharacter.all_objects.get(pk=target_id)
        except BookCharacter.DoesNotExist:
            return Response(
                {"detail": "Target character not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.book_id != source.book_id:
            return Response(
                {"detail": "Target character must belong to the same book."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            _perform_merge(source, target)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target.refresh_from_db()
        return Response(BookCharacterSerializer(target).data)


def _perform_merge(source, target):
    with transaction.atomic():
        # Lock BOTH rows — serializes concurrent merges on same source/target
        source_locked = (
            BookCharacter.all_objects.select_for_update().get(pk=source.pk)
        )
        target_locked = (
            BookCharacter.all_objects.select_for_update().get(pk=target.pk)
        )

        # Re-check preconditions under lock — race-free
        if source_locked.canonical_id is not None:
            raise ValueError("Source is already an alias")
        if target_locked.canonical_id is not None:
            raise ValueError("Target is an alias")

        # 1. Re-point any aliases of source to target
        source_locked.aliases.all().update(canonical=target_locked)

        # 2. Build set of existing (from_id, to_id) pairs NOT involving source
        existing = set(
            CharacterRelationship.objects.filter(book=source_locked.book)
            .exclude(Q(from_character=source_locked) | Q(to_character=source_locked))
            .values_list("from_character_id", "to_character_id")
        )

        # 3. Re-point source's relations to target, deduplicating
        for rel in CharacterRelationship.objects.filter(
            Q(from_character=source_locked) | Q(to_character=source_locked)
        ):
            new_from = (
                target_locked.pk if rel.from_character_id == source_locked.pk
                else rel.from_character_id
            )
            new_to = (
                target_locked.pk if rel.to_character_id == source_locked.pk
                else rel.to_character_id
            )

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
        BookCharacter.all_objects.filter(pk=target_locked.pk).update(
            mention_count=F("mention_count") + source_locked.mention_count
        )

        # 5. Mark source as alias
        source_locked.canonical = target_locked
        source_locked.is_hidden = True
        source_locked.save(update_fields=["canonical_id", "is_hidden"])
