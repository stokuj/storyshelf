from django.db import transaction
from rest_framework import serializers

from library.models import Author, Genre, Serie, Tag
from library.serializers import SerieSerializer

from .models import Book, BookAuthor, BookGenre, BookTag


class _SerieWriteSerializer(serializers.Serializer):
    name = serializers.CharField()


class BookListSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = ["id", "title", "slug", "cover_url", "authors", "genres", "avg_rating", "year"]


class BookDetailSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)
    tags = serializers.StringRelatedField(many=True)
    serie = SerieSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            "title", "slug", "cover_url", "authors", "genres", "tags", "serie",
            "description", "page_count", "isbn", "avg_rating", "year",
            "position_in_series", "ratings_count", "created_at", "updated_at",
        ]


class BookWriteSerializer(serializers.ModelSerializer):
    authors = serializers.ListField(child=serializers.CharField(), write_only=True)
    genres = serializers.ListField(child=serializers.CharField(), write_only=True)
    tags = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False, default=list
    )
    serie = _SerieWriteSerializer(required=False, write_only=True)

    class Meta:
        model = Book
        fields = [
            "title", "year", "isbn", "description", "page_count", "cover_url",
            "avg_rating", "serie", "authors", "genres", "tags", "position_in_series",
        ]

    def _resolve_m2m(self, names, model_cls, normalize):
        objs = []
        for raw in names:
            if normalize == "title":
                normalized = raw.strip().title()
            else:
                normalized = raw.strip().lower()
            obj, _ = model_cls.objects.get_or_create(
                defaults={"name": normalized},
                **{"name__iexact": normalized},
            )
            objs.append(obj)
        return objs

    def _set_m2m(self, book, names, model_cls, normalize, through_cls, rel_attr):
        through_cls.objects.filter(book=book).delete()
        for obj in self._resolve_m2m(names, model_cls, normalize):
            through_cls.objects.create(book=book, **{rel_attr: obj})

    @transaction.atomic
    def create(self, validated_data):
        authors_data = validated_data.pop("authors", [])
        genres_data = validated_data.pop("genres", [])
        tags_data = validated_data.pop("tags", [])
        serie_data = validated_data.pop("serie", None)

        if serie_data:
            serie, _ = Serie.objects.get_or_create(name=serie_data["name"])
            validated_data["serie"] = serie

        book = Book.objects.create(**validated_data)
        self._set_m2m(book, authors_data, Author, "title", BookAuthor, "author")
        self._set_m2m(book, genres_data, Genre, "lower", BookGenre, "genre")
        self._set_m2m(book, tags_data, Tag, "lower", BookTag, "tag")
        return book

    @transaction.atomic
    def update(self, instance, validated_data):
        authors_data = validated_data.pop("authors", None)
        genres_data = validated_data.pop("genres", None)
        tags_data = validated_data.pop("tags", None)
        serie_data = validated_data.pop("serie", None)

        if serie_data:
            serie, _ = Serie.objects.get_or_create(name=serie_data["name"])
            instance.serie = serie
        elif serie_data is not None:
            instance.serie = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if authors_data is not None:
            self._set_m2m(instance, authors_data, Author, "title", BookAuthor, "author")
        if genres_data is not None:
            self._set_m2m(instance, genres_data, Genre, "lower", BookGenre, "genre")
        if tags_data is not None:
            self._set_m2m(instance, tags_data, Tag, "lower", BookTag, "tag")

        return instance
