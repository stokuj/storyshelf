from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    bookTitle = serializers.CharField(source="book.title", read_only=True)
    bookId = serializers.IntegerField(source="book.id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "username",
            "rating",
            "content",
            "createdAt",
            "bookTitle",
            "bookId",
        )
        read_only_fields = ("id", "username", "bookTitle", "bookId", "createdAt")


class ReviewCreateSerializer(serializers.ModelSerializer):
    bookId = serializers.IntegerField(source="book_id")

    class Meta:
        model = Review
        fields = ("id", "rating", "content", "bookId")
        read_only_fields = ("id",)

    def validate(self, data):
        user = self.context["request"].user
        book_id = data.get("book_id")
        if self.instance is None and Review.objects.filter(user=user, book_id=book_id).exists():
            raise serializers.ValidationError("You have already reviewed this book.")
        return data
