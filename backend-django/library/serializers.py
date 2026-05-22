from rest_framework import serializers

from .models import Author, Genre, Serie


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "name", "bio", "birth_date")


class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = ("id", "name", "description", "status")


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")
