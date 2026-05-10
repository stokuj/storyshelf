from rest_framework import serializers
from .models import Book, Chapter, BookCharacter, CharacterRelation


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
    id = serializers.IntegerField(source="character.id")
    name = serializers.CharField(source="character.name")

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "mention_count", "role")


class CharacterRelationSerializer(serializers.ModelSerializer):
    source_character_name = serializers.CharField(source="source.name")
    target_character_name = serializers.CharField(source="target.name")

    class Meta:
        model = CharacterRelation
        fields = (
            "id",
            "source_character_name",
            "target_character_name",
            "relation",
            "evidence",
            "confidence",
        )


class BookSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.JSONField(default=list)
    tags_display = serializers.SerializerMethodField()

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
            "tags_display",
            "rating",
            "ratings_count",
        )

    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_tags_display(self, obj):
        return [t.name for t in obj.tags.all()]


class BookCreateSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField()
    genres = serializers.JSONField(default=list)
    tags = serializers.ListField(
        child=serializers.CharField(), write_only=True, default=list
    )

    class Meta:
        model = Book
        fields = (
            "title",
            "author_id",
            "year",
            "isbn",
            "description",
            "page_count",
            "genres",
            "tags",
        )


class BookDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.JSONField(default=list)
    tags_display = serializers.SerializerMethodField()
    analysis_status = serializers.SerializerMethodField()
    chapters = serializers.SerializerMethodField()
    characters = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    shelf_entry = serializers.SerializerMethodField()

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
            "tags_display",
            "rating",
            "ratings_count",
            "analysis_status",
            "chapters",
            "characters",
            "relations",
            "reviews",
            "shelf_entry",
        )

    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_tags_display(self, obj):
        return [t.name for t in obj.tags.all()]

    def get_analysis_status(self, obj):
        finished = (
            obj.ner_completed_count >= obj.chapters_count
            if obj.chapters_count > 0
            else False
        )
        return {
            "chapters_count": obj.chapters_count,
            "ner_completed_count": obj.ner_completed_count,
            "analysis_finished": finished,
        }

    def get_chapters(self, obj):
        return ChapterSerializer(
            obj.chapters.order_by("chapter_number"), many=True
        ).data

    def get_characters(self, obj):
        return BookCharacterSerializer(
            obj.bookcharacter_set.select_related("character"), many=True
        ).data

    def get_relations(self, obj):
        return CharacterRelationSerializer(
            obj.character_relations.select_related("source", "target"), many=True
        ).data

    def get_reviews(self, obj):
        from reviews.serializers import ReviewSerializer

        return ReviewSerializer(
            obj.reviews.select_related("user").order_by("-created_at"), many=True
        ).data

    def get_shelf_entry(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                entry = obj.shelf_entries.get(user=request.user)
                from shelf.serializers import ShelfEntrySerializer

                return ShelfEntrySerializer(entry).data
            except Exception:
                pass
        return None
