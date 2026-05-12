from rest_framework import generics, permissions
from .models import Author, Genre, Serie
from .serializers import AuthorSerializer, GenreSerializer, SeriesSerializer


class IsModeratorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in (
            "MODERATOR",
            "ADMIN",
        )


class AuthorListCreateView(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsModeratorOrReadOnly]
    pagination_class = None


class AuthorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsModeratorOrReadOnly]


class SeriesListCreateView(generics.ListCreateAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [IsModeratorOrReadOnly]
    pagination_class = None


class SeriesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Serie.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [IsModeratorOrReadOnly]


class GenreListCreateView(generics.ListCreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsModeratorOrReadOnly]
    pagination_class = None


class GenreRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsModeratorOrReadOnly]
