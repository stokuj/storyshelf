from rest_framework import serializers

from books.models import Book

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book"
    )

    class Meta:
        model = Rating
        fields = ["id", "book_slug", "rating"]
        read_only_fields = ["id"]
