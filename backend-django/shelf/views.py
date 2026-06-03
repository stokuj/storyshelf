from django.db.models import Count, Exists, OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from ratings.models import Rating
from users.models import User

from .models import Shelf, ShelfEntry, ShelfMembership
from .serializers import (
    PublicShelfDetailSerializer,
    PublicShelfSerializer,
    ShelfBookSerializer,
    ShelfDetailSerializer,
    ShelfEntrySerializer,
    ShelfSerializer,
)


class ShelfEntryViewSet(viewsets.ModelViewSet):
    serializer_class = ShelfEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user_rating = Rating.objects.filter(
            user=OuterRef("user"), book=OuterRef("book")
        ).values("rating")[:1]
        qs = (
            ShelfEntry.objects.filter(user=self.request.user)
            .annotate(user_rating=Subquery(user_rating))
            .select_related("book")
            .prefetch_related("book__authors", "book__genres")
            .order_by("-created_at")
        )
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShelfViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    lookup_field = "slug"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        return ShelfDetailSerializer if self.action == "retrieve" else ShelfSerializer

    def get_queryset(self):
        qs = (
            Shelf.objects.filter(owner=self.request.user)
            .annotate(book_count=Count("memberships"))
            .order_by("-created_at")
        )
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.annotate(
                contains_book=Exists(
                    ShelfMembership.objects.filter(
                        shelf=OuterRef("pk"), book__slug=book_slug
                    )
                )
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="books")
    def add_book(self, request, slug=None):
        shelf = self.get_object()
        book = get_object_or_404(Book, slug=request.data.get("book_slug"))
        _, created = ShelfMembership.objects.get_or_create(shelf=shelf, book=book)
        return Response(
            ShelfBookSerializer(book).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["delete"], url_path=r"books/(?P<book_slug>[^/.]+)")
    def remove_book(self, request, slug=None, book_slug=None):
        shelf = self.get_object()
        ShelfMembership.objects.filter(shelf=shelf, book__slug=book_slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _public_owner_or_404(request, handle):
    owner = get_object_or_404(User, handle=handle)
    # Profile gates shelves: a private profile hides all shelves from others.
    if not owner.profile_public and owner != request.user:
        raise Http404("No User matches the given query.")
    return owner


class PublicShelfListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicShelfSerializer
    pagination_class = None

    def get_queryset(self):
        owner = _public_owner_or_404(self.request, self.kwargs["handle"])
        return (
            Shelf.objects.filter(owner=owner, is_public=True)
            .annotate(book_count=Count("memberships"))
            .order_by("-created_at")
        )


class PublicShelfDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicShelfDetailSerializer

    def get_object(self):
        owner = _public_owner_or_404(self.request, self.kwargs["handle"])
        return get_object_or_404(
            Shelf, owner=owner, slug=self.kwargs["slug"], is_public=True
        )
