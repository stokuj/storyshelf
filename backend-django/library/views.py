from rest_framework import generics, permissions
from .models import Author, Serie
from .serializers import AuthorSerializer, SeriesSerializer


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
