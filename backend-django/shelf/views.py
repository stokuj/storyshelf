from django.db.models import OuterRef, Subquery
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ratings.models import Rating

from .models import ShelfEntry
from .serializers import ShelfEntrySerializer


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
