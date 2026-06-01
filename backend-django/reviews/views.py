from django.db.models import OuterRef, Subquery
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from books.models import Book
from ratings.models import Rating

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ["get", "put", "delete", "head", "options"]

    def get_permissions(self):
        # Public read (list/retrieve); write/delete/me require auth.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        author_rating = Rating.objects.filter(
            user=OuterRef("user"), book=OuterRef("book")
        ).values("rating")[:1]
        qs = (
            Review.objects.annotate(author_rating=Subquery(author_rating))
            .select_related("user", "book")
            .order_by("-created_at")
        )
        # Destroy is scoped to the owner so users can't delete others' reviews.
        if self.action == "destroy":
            qs = qs.filter(user=self.request.user)
        book_slug = self.request.query_params.get("book_slug")
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def update(self, request, *args, **kwargs):
        """PUT = upsert on (user, book). 201 if created, 200 if updated."""
        book_slug = request.data.get("book_slug")
        try:
            book = Book.objects.get(slug=book_slug)
        except Book.DoesNotExist:
            return Response({"book_slug": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review, created = Review.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={"body": serializer.validated_data["body"]},
        )
        annotated = self.get_queryset().get(pk=review.pk)
        out = self.get_serializer(annotated)
        return Response(
            out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        book_slug = request.query_params.get("book_slug")
        qs = self.get_queryset().filter(user=request.user)
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        review = qs.first()
        if review is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(review).data)
