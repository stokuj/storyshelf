from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import ShelfEntry
from .serializers import ShelfEntrySerializer


class ShelfListView(generics.ListAPIView):
    """
    Zwraca wszystkie wpisy na półce zalogowanego użytkownika, sortowane od najnowszego.
    Statusy: WANT_TO_READ | READING | READ.
    """

    serializer_class = ShelfEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # flat list for frontend

    def get_queryset(self):
        return (
            ShelfEntry.objects.filter(user=self.request.user)
            .select_related("book")
            .prefetch_related("book__authors")
            .order_by("-created_at")
        )


class ShelfEntryView(APIView):
    """
    Zarządzanie pojedynczym wpisem na półce dla książki o podanym book_id.
    GET: Pobierz wpis (404 jeśli książka nie jest na półce).
    POST: Dodaj książkę na półkę (domyślny status: WANT_TO_READ). Idempotentne — nie duplikuje.
    PATCH: Zmień status (wymagane pole: status).
    DELETE: Usuń książkę z półki.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        return Response(ShelfEntrySerializer(entry).data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        status_val = request.data.get("status", "WANT_TO_READ")
        valid_statuses = {s.value for s in ShelfEntry.Status}
        if status_val not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Choose from: {', '.join(valid_statuses)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
            return Response({"detail": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        valid_statuses = {s.value for s in ShelfEntry.Status}
        if status_val not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Choose from: {', '.join(valid_statuses)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entry.status = status_val
        entry.start_date = request.data.get("start_date", entry.start_date)
        entry.finish_date = request.data.get("finish_date", entry.finish_date)
        try:
            entry.full_clean()
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        entry.save()
        return Response(ShelfEntrySerializer(entry).data)

    def delete(self, request, book_id):
        entry = get_object_or_404(ShelfEntry, user=request.user, book_id=book_id)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
