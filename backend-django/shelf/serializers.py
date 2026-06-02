from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from books.models import Book

from .models import ShelfEntry


class ShelfBookSerializer(serializers.ModelSerializer):
    # StringRelatedField → list[str], matching the M2 Book serializer and the
    # frontend `Book` type (authors: string[], genres: string[]).
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = ["slug", "title", "cover_url", "authors", "genres", "avg_rating", "page_count"]


class ShelfEntrySerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book", write_only=True
    )
    book = ShelfBookSerializer(read_only=True)
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = ShelfEntry
        fields = [
            "id",
            "book_slug",
            "status",
            "start_date",
            "finish_date",
            "current_page",
            "user_rating",
            "book",
        ]
        read_only_fields = ["id", "book", "user_rating"]

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_user_rating(self, obj):
        # Populated by the view's Subquery annotation on list/retrieve;
        # absent on a freshly created instance → None.
        return getattr(obj, "user_rating", None)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        book = attrs.get("book", getattr(self.instance, "book", None))

        # Uniqueness (user is not a serializer field, so DRF can't auto-check it).
        if self.instance is None and ShelfEntry.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError(
                {"book_slug": "This book is already on your shelf."}
            )

        # Book is immutable after creation.
        if self.instance is not None and "book" in attrs:
            raise serializers.ValidationError(
                {"book_slug": "Cannot change the book of an existing shelf entry."}
            )

        # Reuse model.clean() for current_page / date validation (DRY).
        entry = self.instance or ShelfEntry()
        entry.user = user
        for field in ("book", "status", "start_date", "finish_date", "current_page"):
            if field in attrs:
                setattr(entry, field, attrs[field])
        try:
            entry.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs
