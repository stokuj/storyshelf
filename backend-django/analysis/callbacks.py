from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book, Chapter, StoryCharacter, BookCharacter, CharacterRelation
from .tasks import find_pairs, relations_for_book


class AnalyseResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, chapter_id):
        chapter = get_object_or_404(
            Chapter.objects.select_related("book"), id=chapter_id
        )
        if chapter.analysis_completed:
            return Response(status=status.HTTP_200_OK)

        data = request.data
        chapter.char_count = (
            data["char_count"] if "char_count" in data else data.get("charCount")
        )
        chapter.char_count_clean = (
            data["char_count_clean"]
            if "char_count_clean" in data
            else data.get("charCountClean")
        )
        chapter.word_count = (
            data["word_count"] if "word_count" in data else data.get("wordCount")
        )
        chapter.token_count = (
            data["token_count"] if "token_count" in data else data.get("tokenCount")
        )
        chapter.analysis_completed = True
        chapter.save()
        return Response(status=status.HTTP_200_OK)


class NerResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, chapter_id):
        with transaction.atomic():
            chapter = (
                Chapter.objects.select_for_update()
                .select_related("book")
                .get(id=chapter_id)
            )
            if chapter.ner_result is not None:
                return Response(status=status.HTTP_200_OK)

            result = request.data.get("result", {})
            characters = result.get("characters", {})
            chapter.ner_result = {"characters": characters}
            chapter.save()

            Book.objects.filter(id=chapter.book_id).update(
                ner_completed_count=F("ner_completed_count") + 1
            )

            book = Book.objects.get(id=chapter.book_id)
            for name, count in characters.items():
                sc, _ = StoryCharacter.objects.get_or_create(name=name)
                bc, created = BookCharacter.objects.get_or_create(
                    book=book,
                    character=sc,
                    defaults={"mention_count": count, "role": None},
                )
                if not created:
                    bc.mention_count = F("mention_count") + count
                    bc.save(update_fields=["mention_count"])

            book.refresh_from_db()
            if book.ner_completed_count >= book.chapters_count:
                find_pairs.delay(book.id)

        return Response(status=status.HTTP_200_OK)


class FindPairsResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, book_id):
        if CharacterRelation.objects.filter(book_id=book_id).exists():
            return Response(status=status.HTTP_200_OK)

        pairs = request.data.get("pairs", [])
        for pair in pairs:
            pair_data = pair.get("pair", [])
            if len(pair_data) >= 2:
                source, _ = StoryCharacter.objects.get_or_create(name=pair_data[0])
                target, _ = StoryCharacter.objects.get_or_create(name=pair_data[1])
                CharacterRelation.objects.get_or_create(
                    book_id=book_id,
                    source=source,
                    target=target,
                )

        relations_for_book.delay(book_id)
        return Response(status=status.HTTP_200_OK)


class RelationsResultView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, book_id):
        all_relations = request.data.get("all_relations", [])
        for result_group in all_relations:
            relations_list = result_group.get("relations", {}).get("relations", [])
            for rel in relations_list:
                source_name = rel.get("source")
                target_name = rel.get("target")
                relation_text = rel.get("relation")
                if not source_name or not target_name:
                    continue

                try:
                    source = StoryCharacter.objects.get(name=source_name)
                    target = StoryCharacter.objects.get(name=target_name)
                    cr = CharacterRelation.objects.filter(
                        book_id=book_id, source=source, target=target
                    ).first()
                    if cr and not cr.relation:
                        cr.relation = relation_text
                        cr.evidence = rel.get("evidence")
                        cr.confidence = rel.get("confidence")
                        cr.save()
                except StoryCharacter.DoesNotExist:
                    pass

        return Response(status=status.HTTP_200_OK)
