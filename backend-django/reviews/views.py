from django.db.models import Count, Exists, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from books.models import Book
from ratings.models import Rating
from users.selectors import public_owner_or_404

from .models import Review, ReviewLike
from .serializers import ReviewSerializer


def annotate_reviews(qs, user):
    """Attach author_rating, likes_count, is_liked to a Review queryset."""
    author_rating = Rating.objects.filter(
        user=OuterRef("user"), book=OuterRef("book")
    ).values("rating")[:1]
    qs = qs.annotate(
        author_rating=Subquery(author_rating),
        likes_count=Count("likes", distinct=True),
    ).select_related("user", "book")
    if user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(ReviewLike.objects.filter(review=OuterRef("pk"), user=user))
        )
    return qs


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ["get", "post", "put", "delete", "head", "options"]

    def get_permissions(self):
        # Public read (list/retrieve); write/delete/me require auth.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = annotate_reviews(Review.objects.all(), self.request.user).order_by("-created_at")
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
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

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
        # get_queryset() already applies the optional ?book_slug filter.
        review = self.get_queryset().filter(user=request.user).first()
        if review is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(review).data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        review = get_object_or_404(Review, pk=pk)
        if request.method == "POST":
            ReviewLike.objects.get_or_create(user=request.user, review=review)
            is_liked = True
        else:
            ReviewLike.objects.filter(user=request.user, review=review).delete()
            is_liked = False
        return Response({"likes_count": review.likes.count(), "is_liked": is_liked})


class UserReviewListView(generics.ListAPIView):
    """Public, paginated reviews by one user, gated by profile_public."""

    permission_classes = [AllowAny]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        owner = public_owner_or_404(self.request, self.kwargs["handle"])
        return annotate_reviews(
            Review.objects.filter(user=owner), self.request.user
        ).order_by("-updated_at")
