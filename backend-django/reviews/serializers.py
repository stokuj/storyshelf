from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)
    book_id = serializers.IntegerField(source="book.id", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "username",
            "rating",
            "content",
            "created_at",
            "book_title",
            "book_id",
        )
        read_only_fields = ("id", "username", "book_title", "book_id", "created_at")
