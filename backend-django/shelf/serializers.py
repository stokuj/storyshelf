from rest_framework import serializers

from books.serializers import BookPreviewSerializer

from .models import Shelf, ShelfEntry


class ShelfEntrySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    startDate = serializers.DateField(source="start_date", read_only=True)
    finishDate = serializers.DateField(source="finish_date", read_only=True)
    personalRating = serializers.IntegerField(source="personal_rating", read_only=True)

    class Meta:
        model = ShelfEntry
        fields = ("book", "status", "startDate", "finishDate", "personalRating", "createdAt")

    def get_book(self, obj):
        author = obj.book.authors.first().name if obj.book.authors.exists() else None
        return {"id": obj.book.id, "title": obj.book.title, "author": author}


class ShelfSerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()
    class Meta:
        model = Shelf
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_public",
            "book_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "book_count", "created_at", "updated_at")

    def get_book_count(self, obj):
        return obj.memberships.count()


class ShelfDetailSerializer(ShelfSerializer):
    books = serializers.SerializerMethodField()

    class Meta(ShelfSerializer.Meta):
        fields = ShelfSerializer.Meta.fields + ("books",)

    def get_books(self, obj):
        memberships = (
            obj.memberships.select_related("book")
            .prefetch_related("book__authors")
            .order_by("position", "-added_at")
        )
        return BookPreviewSerializer(
            [m.book for m in memberships], many=True, context=self.context
        ).data


class ShelfCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = ("name", "description", "is_public")

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return value.strip()
