from django.db import IntegrityError
from rest_framework import generics, permissions
from rest_framework import status as http_status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer, ScopedReviewCreateSerializer


def _handle_integrity_error():
    return Response(
        {"detail": "You have already reviewed this book."},
        status=http_status.HTTP_400_BAD_REQUEST,
    )


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET: Płaska lista recenzji, sortowana od najnowszej.
         Filtry: ?book_id=<id> — recenzje danej książki;
         ?user_id=<id> — recenzje danego użytkownika.
    POST: Utwórz recenzję (wymaga logowania). Jedno konto może wystawić max 1 recenzję per książka.
          Po zapisie sygnał Django automatycznie aktualizuje Book.avg_rating i Book.ratings_count.
    """

    # default pagination from settings

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related("user", "book").order_by("-created_at")
        book_id = self.request.query_params.get("book_id")
        if book_id:
            qs = qs.filter(book_id=book_id)
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return _handle_integrity_error()


class BookReviewListCreateView(generics.ListCreateAPIView):
    """Scoped reviews for a single book: GET /books/:id/reviews/, POST /books/:id/reviews/."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ScopedReviewCreateSerializer
        return ReviewSerializer

    def _get_book(self):
        if not hasattr(self, "_book"):
            from books.lookups import resolve_book
            self._book = resolve_book(self.kwargs["id_or_slug"])
        return self._book

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["book"] = self._get_book()
        return ctx

    def get_queryset(self):
        book = self._get_book()
        return (
            Review.objects.filter(book=book)
            .select_related("user", "book")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, book=self._get_book())

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return _handle_integrity_error()


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Szczegóły recenzji — publiczne.
    PUT/PATCH: Edycja recenzji — tylko autor recenzji.
    DELETE: Usunięcie recenzji — tylko autor recenzji. Sygnał przelicza avg_rating książki.
    """

    serializer_class = ReviewSerializer
    queryset = Review.objects.select_related("user", "book").all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()
