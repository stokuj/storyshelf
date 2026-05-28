from rest_framework import serializers

from .models import Author, Genre, Serie, Tag


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio", "birth_date"]


class SerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = ["id", "name", "description", "status", "created_at"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
