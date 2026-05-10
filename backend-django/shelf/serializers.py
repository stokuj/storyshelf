from rest_framework import serializers
from .models import ShelfEntry


class ShelfEntrySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = ShelfEntry
        fields = ("book", "status", "created_at")

    def get_book(self, obj):
        author = obj.book.authors.first().name if obj.book.authors.exists() else None
        return {"id": obj.book.id, "title": obj.book.title, "author": author}
