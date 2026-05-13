from django.db import models
from rest_framework import serializers
from .models import Book, Chapter
from analysis.models import BookCharacter, CharacterRelationship


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = (
            "id",
            "book_id",
            "chapter_number",
            "title",
            "analysis_completed",
            "char_count",
            "char_count_clean",
            "word_count",
            "token_count",
        )
        read_only_fields = ("book_id", "analysis_completed")


class BookCharacterSerializer(serializers.ModelSerializer):
    mentionCount = serializers.IntegerField(source="mention_count")

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "description", "mentionCount")


class CharacterRelationSerializer(serializers.ModelSerializer):
    sourceCharacterName = serializers.CharField(source="from_character.name")
    targetCharacterName = serializers.CharField(source="to_character.name")

    class Meta:
        model = CharacterRelationship
        fields = (
            "id",
            "sourceCharacterName",
            "targetCharacterName",
            "relation_type",
        )


class BookSerializerMixin:
    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_genres(self, obj):
        return [g.name for g in obj.genres.all()]

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]


class BookListSerializer(BookSerializerMixin, serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "year",
            "isbn",
            "description",
            "page_count",
            "genres",
            "tags",
            "avg_rating",
            "ratings_count",
        )


class BookDetailSerializer(BookSerializerMixin, serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    ratingsCount = serializers.IntegerField(source="ratings_count")

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "year",
            "isbn",
            "description",
            "page_count",
            "genres",
            "tags",
            "avg_rating",
            "ratingsCount",
        )

    def to_representation(self, instance):
        request = self.context.get("request")

        # Build book object
        book_data = super().to_representation(instance)

        # Analysis status
        finished = (
            instance.ner_completed_count >= instance.chapters_count
            if instance.chapters_count > 0
            else False
        )
        book_data["analysisStatus"] = {
            "chaptersCount": instance.chapters_count,
            "nerCompletedCount": instance.ner_completed_count,
            "analysisFinished": finished,
        }

        # Series info (fallbacks for frontend)
        if instance.serie:
            book_data["series"] = {"name": instance.serie.name}
        book_data["seriesName"] = instance.serie.name if instance.serie else None
        book_data["seriesTitle"] = None

        # Shelf entry
        shelf_entry = None
        if request and request.user.is_authenticated:
            try:
                entry = instance.shelf_entries.get(user=request.user)
                shelf_entry = {
                    "status": entry.status,
                    "createdAt": entry.created_at.isoformat(),
                }
            except Exception:
                pass

        # Chapters
        chapters = ChapterSerializer(instance.chapters.order_by("chapter_number"), many=True).data

        # Characters
        characters = BookCharacterSerializer(
            BookCharacter.objects.filter(
                models.Q(relations_from__book_id=instance.id)
                | models.Q(relations_to__book_id=instance.id)
            ).distinct(),
            many=True,
        ).data

        # Relations
        relations = CharacterRelationSerializer(
            instance.character_relationships.select_related("from_character", "to_character"),
            many=True,
        ).data

        # Reviews
        from reviews.serializers import ReviewSerializer

        reviews = ReviewSerializer(
            instance.reviews.select_related("user").order_by("-created_at"), many=True
        ).data

        return {
            "book": book_data,
            "shelfEntry": shelf_entry,
            "chapters": chapters,
            "reviews": reviews,
            "characters": characters,
            "relations": relations,
        }
