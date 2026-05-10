from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ShelfEntry
from books.models import Book
from .serializers import ShelfEntrySerializer


class ShelfListView(generics.ListAPIView):
    serializer_class = ShelfEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ShelfEntry.objects.filter(user=self.request.user)
            .select_related("book")
            .order_by("-created_at")
        )


class ShelfEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        return Response(ShelfEntrySerializer(entry).data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        status_val = request.data.get("status", "WANT_TO_READ")
        entry, _ = ShelfEntry.objects.get_or_create(
            user=request.user, book=book, defaults={"status": status_val}
        )
        return Response(
            ShelfEntrySerializer(entry).data, status=status.HTTP_201_CREATED
        )

    def patch(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        status_val = request.data.get("status")
        if not status_val:
            return Response({"detail": "status required"}, status=400)
        entry.status = status_val
        entry.save()
        return Response(ShelfEntrySerializer(entry).data)

    def delete(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
