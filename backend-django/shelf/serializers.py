from rest_framework import serializers

from .models import ShelfEntry


class ShelfEntrySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ShelfEntry
        fields = ("book", "status", "createdAt")

    def get_book(self, obj):
        author = obj.book.authors.first().name if obj.book.authors.exists() else None
        return {"id": obj.book.id, "title": obj.book.title, "author": author}
