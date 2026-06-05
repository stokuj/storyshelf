from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

from books.models import Book

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book", write_only=True
    )
    author = serializers.SerializerMethodField()
    author_rating = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Review
        fields = [
            "id",
            "book_slug",
            "body",
            "author",
            "author_rating",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "author_rating",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(
        inline_serializer(
            name="ReviewAuthor",
            fields={
                "handle": serializers.CharField(),
                "display_name": serializers.CharField(),
            },
        )
    )
    def get_author(self, obj):
        return {"handle": obj.user.handle, "display_name": obj.user.display_name}

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_author_rating(self, obj):
        # Populated by the view's Subquery annotation on list; None otherwise.
        return getattr(obj, "author_rating", None)

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Review body cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError("Review body cannot exceed 5000 characters.")
        return value
