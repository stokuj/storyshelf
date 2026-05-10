from rest_framework import serializers
from .models import Author, Serie, Tag


class AuthorSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ("id", "name", "bio", "avatar_url", "birth_date")

    def get_avatar_url(self, obj):
        return None


class SeriesSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Serie
        fields = ("id", "name", "description", "cover_url", "status")

    def get_cover_url(self, obj):
        return None
