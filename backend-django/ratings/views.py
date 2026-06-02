from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book

from .models import Rating
from .serializers import RatingSerializer


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # GET returns a plain list (own ratings)
    http_method_names = ["get", "put", "delete", "head", "options"]

    def get_queryset(self):
        qs = Rating.objects.filter(user=self.request.user).select_related("book")
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
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate the rating value via the serializer (honours 1..5 validators).
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={"rating": serializer.validated_data["rating"]},
        )
        out = self.get_serializer(rating)
        return Response(
            out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
