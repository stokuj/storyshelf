from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from books.models import Book

from .models import Review
from .serializers import ReviewSerializer


class IsAdminForDelete(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_authenticated and request.user.role == "ADMIN"
        return True


class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    pagination_class = None  # flat list for frontend

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
    permission_classes = [permissions.IsAuthenticated, IsAdminForDelete]
