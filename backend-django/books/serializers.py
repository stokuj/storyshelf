from rest_framework import serializers

from analysis.models import BookCharacter
from analysis.serializers import BookCharacterSerializer, CharacterRelationSerializer

from .models import Book


class BookPreviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ("id", "slug", "title", "author", "avg_rating")

    def get_author(self, obj):
        authors = list(obj.authors.all())
        return authors[0].name if authors else None


class BookListSerializer(serializers.ModelSerializer):
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

    def get_author(self, obj):
        # Prefetched via Prefetch("authors", to_attr="_prefetched_authors") in BookListView
        authors = list(obj.authors.all())
        return authors[0].name if authors else None

    def get_genres(self, obj):
        return [g.name for g in obj.genres.all()]

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]


class BookDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    ratingsCount = serializers.IntegerField(source="ratings_count")  # noqa: N815

    def get_author(self, obj):
        authors = list(obj.authors.all())
        return authors[0].name if authors else None

    def get_genres(self, obj):
        return [g.name for g in obj.genres.all()]

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]

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

        is_admin = self.context.get("is_admin", False)

        book_data["analysisStatus"] = {
            "analysisFinished": instance.ai_extraction_status == "done",
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

        # Use view-side Prefetch (to_attr="_prefetched_characters") to avoid re-query.
        chars = getattr(instance, "_prefetched_characters", None)
        if chars is None:
            chars_qs = (
                BookCharacter.all_objects.filter(book=instance, canonical__isnull=True) if is_admin
                else instance.characters.filter(canonical__isnull=True)
            )
            chars = chars_qs
        characters = BookCharacterSerializer(chars, many=True).data

        rels_qs = instance.character_relationships.all()
        if not is_admin:
            rels_qs = rels_qs.filter(
                from_character__is_hidden=False,
                to_character__is_hidden=False,
            )
        relations = CharacterRelationSerializer(rels_qs, many=True).data

        return {
            "book": book_data,
            "shelfEntry": shelf_entry,
            "characters": characters,
            "relations": relations,
        }
