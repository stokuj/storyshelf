from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from config.pagination import StandardPagination

from .models import Book
from .permissions import IsAdminOrReadOnly
from .serializers import BookDetailSerializer, BookListSerializer, BookWriteSerializer


class BookPagination(StandardPagination):
    page_size = 12


class BookViewSet(ModelViewSet):
    queryset = Book.objects.prefetch_related("authors", "genres", "tags").select_related("serie")
    serializer_class = BookDetailSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = BookPagination
    lookup_field = "slug"
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "authors__name"]
    ordering_fields = ["title", "year", "avg_rating"]
    ordering = ["title"]

    def get_queryset(self):
        qs = super().get_queryset()
        author = self.request.query_params.get("author")
        genre = self.request.query_params.get("genre")
        year_min = self.request.query_params.get("year_min")
        year_max = self.request.query_params.get("year_max")
        if author:
            qs = qs.filter(authors__name__icontains=author)
        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        if year_min:
            qs = qs.filter(year__gte=year_min)
        if year_max:
            qs = qs.filter(year__lte=year_max)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BookWriteSerializer
        return BookDetailSerializer
