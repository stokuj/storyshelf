from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from books.models import Book

from .models import Shelf, ShelfEntry


class ShelfBookSerializer(serializers.ModelSerializer):
    # StringRelatedField → list[str], matching the M2 Book serializer and the
    # frontend `Book` type (authors: string[], genres: string[]).
    authors = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = ["slug", "title", "cover_url", "authors", "genres", "avg_rating", "page_count"]


class ShelfEntrySerializer(serializers.ModelSerializer):
    book_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Book.objects.all(), source="book", write_only=True
    )
    book = ShelfBookSerializer(read_only=True)
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = ShelfEntry
        fields = [
            "id",
            "book_slug",
            "status",
            "start_date",
            "finish_date",
            "current_page",
            "user_rating",
            "book",
        ]
        read_only_fields = ["id", "book", "user_rating"]

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_user_rating(self, obj):
        # Populated by the view's Subquery annotation on list/retrieve;
        # absent on a freshly created instance → None.
        return getattr(obj, "user_rating", None)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        book = attrs.get("book", getattr(self.instance, "book", None))

        # Uniqueness (user is not a serializer field, so DRF can't auto-check it).
        if self.instance is None and ShelfEntry.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError(
                {"book_slug": "This book is already on your shelf."}
            )

        # Book is immutable after creation.
        if self.instance is not None and "book" in attrs:
            raise serializers.ValidationError(
                {"book_slug": "Cannot change the book of an existing shelf entry."}
            )

        # Auto-set finish_date the first time an entry becomes READ, so reading
        # stats (books/year, time-on-shelf) have a date to work with. Never
        # overwrite an existing or explicitly-provided finish_date.
        result_status = attrs.get("status", getattr(self.instance, "status", None))
        if (
            result_status == ShelfEntry.Status.READ
            and "finish_date" not in attrs
            and getattr(self.instance, "finish_date", None) is None
        ):
            attrs["finish_date"] = timezone.localdate()

        # Reuse model.clean() for current_page / date validation (DRY).
        entry = self.instance or ShelfEntry()
        entry.user = user
        for field in ("book", "status", "start_date", "finish_date", "current_page"):
            if field in attrs:
                setattr(entry, field, attrs[field])
        try:
            entry.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs


class ShelfSerializer(serializers.ModelSerializer):
    """List/create/update view of a shelf (no books)."""

    book_count = serializers.SerializerMethodField()
    contains_book = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_public",
            "book_count",
            "contains_book",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "book_count", "contains_book", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_book_count(self, obj):
        # Annotated by the view; fall back to a count for un-annotated instances.
        count = getattr(obj, "book_count", None)
        return count if count is not None else obj.memberships.count()

    @extend_schema_field(serializers.BooleanField(allow_null=True))
    def get_contains_book(self, obj):
        # Only annotated when the list view is filtered by ?book_slug; else None.
        return getattr(obj, "contains_book", None)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Shelf name cannot be empty.")
        # owner is set in the view (not a serializer field) → check uniqueness here.
        # Case-insensitive so "Fantasy" and "fantasy" can't coexist for one owner.
        user = self.context["request"].user
        qs = Shelf.objects.filter(owner=user, name__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a shelf with this name.")
        return value


class ShelfDetailSerializer(ShelfSerializer):
    """Retrieve view: shelf + its books (newest first)."""

    books = serializers.SerializerMethodField()

    class Meta(ShelfSerializer.Meta):
        fields = ShelfSerializer.Meta.fields + ["books"]

    @extend_schema_field(ShelfBookSerializer(many=True))
    def get_books(self, obj):
        books = [
            m.book
            for m in obj.memberships.select_related("book").prefetch_related(
                "book__authors", "book__genres"
            )
        ]
        return ShelfBookSerializer(books, many=True).data


class PublicShelfSerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = ["name", "slug", "description", "book_count", "created_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_book_count(self, obj):
        count = getattr(obj, "book_count", None)
        return count if count is not None else obj.memberships.count()


class PublicShelfDetailSerializer(PublicShelfSerializer):
    books = serializers.SerializerMethodField()

    class Meta(PublicShelfSerializer.Meta):
        fields = PublicShelfSerializer.Meta.fields + ["books"]

    @extend_schema_field(ShelfBookSerializer(many=True))
    def get_books(self, obj):
        books = [
            m.book
            for m in obj.memberships.select_related("book").prefetch_related(
                "book__authors", "book__genres"
            )
        ]
        return ShelfBookSerializer(books, many=True).data
