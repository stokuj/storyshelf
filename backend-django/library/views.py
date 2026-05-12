from rest_framework import generics, permissions

from .models import Author, Genre, Serie
from .serializers import AuthorSerializer, GenreSerializer, SeriesSerializer


class AuthorListView(generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class AuthorRetrieveView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]


class SeriesListView(generics.ListAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SeriesRetrieveView(generics.RetrieveAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.AllowAny]


class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class GenreRetrieveView(generics.RetrieveAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
