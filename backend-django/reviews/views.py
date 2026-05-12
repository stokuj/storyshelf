from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from books.models import Book

from .models import Review
from .serializers import ReviewSerializer


class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Review.objects.filter(book_id=self.kwargs["pk"])
            .select_related("user", "book")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        book = get_object_or_404(Book, id=self.kwargs["pk"])
        serializer.save(user=self.request.user, book=book)


class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        return obj
