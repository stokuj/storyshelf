from rest_framework import serializers

from analysis.models import BookCharacter, CharacterRelationship

from .models import Book


class BookCharacterSerializer(serializers.ModelSerializer):
    mentionCount = serializers.IntegerField(source="mention_count")  # noqa: N815

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "description", "mentionCount")


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
    ratingsCount = serializers.IntegerField(source="ratings_count")  # noqa: N815

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
        book_data = super().to_representation(instance)

        book_data["analysisStatus"] = {
            "analysisFinished": BookCharacter.objects.filter(book=instance).exists(),
        }

        if instance.serie:
            book_data["series"] = {"name": instance.serie.name}
        book_data["seriesName"] = instance.serie.name if instance.serie else None
        book_data["seriesTitle"] = None

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

        characters = BookCharacterSerializer(
            instance.characters.all(),
            many=True,
        ).data

        relations = CharacterRelationSerializer(
            instance.character_relationships.select_related("from_character", "to_character"),
            many=True,
        ).data

        return {
            "book": book_data,
            "shelfEntry": shelf_entry,
            "characters": characters,
            "relations": relations,
        }
