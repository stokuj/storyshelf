from rest_framework import generics, permissions

from .models import Author, Genre, Serie
from .serializers import AuthorSerializer, GenreSerializer, SeriesSerializer


class AuthorListView(generics.ListAPIView):
    """Płaska lista wszystkich autorów. Tylko odczyt — zarządzanie przez Django Admin."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class AuthorRetrieveView(generics.RetrieveAPIView):
    """Szczegóły autora: imię, bio, data urodzenia.

    avatar_url zarezerwowany na przyszłość (obecnie null).
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]


class SeriesListView(generics.ListAPIView):
    """Płaska lista wszystkich serii. Tylko odczyt — zarządzanie przez Django Admin."""

    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SeriesRetrieveView(generics.RetrieveAPIView):
    """Szczegóły serii: nazwa, opis, status (ONGOING/COMPLETED/CANCELLED/HIATUS).

    cover_url obecnie null.
    """

    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]


class GenreListView(generics.ListAPIView):
    """Płaska lista wszystkich gatunków, sortowana alfabetycznie. Tylko odczyt."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class GenreRetrieveView(generics.RetrieveAPIView):
    """Szczegóły gatunku."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
