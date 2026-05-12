from rest_framework import serializers
from .models import Book, Chapter


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


class BookListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.JSONField(default=list)
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

    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]


class BookCreateSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(write_only=True)
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

    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]

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
        chapters = ChapterSerializer(
            instance.chapters.order_by("chapter_number"), many=True
        ).data

        # Characters (TODO: rewire in follow-up task)
        characters = []

        # Relations (TODO: rewire in follow-up task)
        relations = []

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
