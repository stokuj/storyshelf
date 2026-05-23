from rest_framework import serializers

from analysis.models import BookCharacter, CharacterRelationship

from .models import Book


class BookCharacterSerializer(serializers.ModelSerializer):
    mention_count = serializers.IntegerField()

    class Meta:
        model = BookCharacter
        fields = (
            "id", "slug", "name", "description",
            "mention_count", "source", "confidence", "is_hidden",
        )


class CharacterRelationSerializer(serializers.ModelSerializer):
    sourceCharacterName = serializers.CharField(source="from_character.name")  # noqa: N815
    targetCharacterName = serializers.CharField(source="to_character.name")  # noqa: N815

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
        # Use the prefetched authors cache to avoid an extra query per book.
        authors = list(obj.authors.all())
        return authors[0].name if authors else None

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
            "slug",
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
    ratingsCount = serializers.IntegerField(source="ratings_count")  # noqa: N815

    class Meta:
        model = Book
        fields = (
            "id",
            "slug",
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
        book_data = super().to_representation(instance)

        is_admin = bool(request and request.user and request.user.is_staff)

        book_data["analysisStatus"] = {
            "analysisFinished": instance.characters.filter(is_hidden=False).exists(),
            "status": instance.ai_extraction_status,
        }
        book_data["seriesName"] = instance.serie.name if instance.serie else None

        shelf_entry = None
        if request and request.user.is_authenticated:
            entries = getattr(instance, "current_user_shelf_entries", None)
            entry = entries[0] if entries else None
            if entry is not None:
                shelf_entry = {
                    "status": entry.status,
                    "createdAt": entry.created_at.isoformat(),
                }

        chars_qs = (
            instance.characters.all() if is_admin
            else instance.characters.filter(is_hidden=False)
        )
        characters = BookCharacterSerializer(chars_qs, many=True).data

        relations = CharacterRelationSerializer(
            instance.character_relationships.all(),
            many=True,
        ).data

        return {
            "book": book_data,
            "shelfEntry": shelf_entry,
            "characters": characters,
            "relations": relations,
        }
