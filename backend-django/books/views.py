from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
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
            # icontains across the authors M2M can match several rows per book,
            # so distinct() is required to avoid duplicate results (which would
            # also inflate the paginated `total`).
            qs = qs.filter(authors__name__icontains=author).distinct()
        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        if year_min:
            try:
                qs = qs.filter(year__gte=int(year_min))
            except (ValueError, TypeError):
                raise ValidationError({"year_min": "Must be an integer."})
        if year_max:
            try:
                qs = qs.filter(year__lte=int(year_max))
            except (ValueError, TypeError):
                raise ValidationError({"year_max": "Must be an integer."})
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BookWriteSerializer
        return BookDetailSerializer

    def _detail_response(self, book, http_status_code):
        """Return a response using BookDetailSerializer (re-fetch with relations)."""
        book.refresh_from_db()
        serializer = BookDetailSerializer(
            Book.objects.prefetch_related("authors", "genres", "tags")
            .select_related("serie")
            .get(pk=book.pk),
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=http_status_code)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        return self._detail_response(book, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        return self._detail_response(book, status.HTTP_200_OK)

