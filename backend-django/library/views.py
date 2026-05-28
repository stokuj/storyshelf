from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Author, Genre, Serie, Tag
from .serializers import AuthorSerializer, GenreSerializer, SerieSerializer, TagSerializer


class AuthorViewSet(ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class SerieViewSet(ReadOnlyModelViewSet):
    queryset = Serie.objects.all()
    serializer_class = SerieSerializer


class GenreViewSet(ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
