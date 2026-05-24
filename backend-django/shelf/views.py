from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import Shelf, ShelfEntry, ShelfMembership
from .serializers import (
    ShelfCreateSerializer,
    ShelfDetailSerializer,
    ShelfEntrySerializer,
    ShelfSerializer,
)


class ShelfListView(generics.ListAPIView):
    """
    Zwraca wszystkie wpisy na półce zalogowanego użytkownika, sortowane od najnowszego.
    Statusy: WANT_TO_READ | READING | READ.
    """

    serializer_class = ShelfEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    # default pagination from settings

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
        entry, created = ShelfEntry.objects.get_or_create(
            user=request.user, book=book, defaults={"status": status_val}
        )
        if created:
            # Apply date fields and validate on create (get_or_create bypasses clean()).
            start_date = request.data.get("start_date")
            finish_date = request.data.get("finish_date")
            if start_date:
                entry.start_date = start_date
            if finish_date:
                entry.finish_date = finish_date
            try:
                entry.full_clean()
            except ValidationError as e:
                entry.delete()  # rollback the get_or_create
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            entry.save(update_fields=["start_date", "finish_date"])
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
        if "personal_rating" in request.data:
            entry.personal_rating = request.data.get("personal_rating")
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


class MyShelvesView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # default pagination from settings

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ShelfCreateSerializer
        return ShelfSerializer

    def get_queryset(self):
        return Shelf.objects.filter(user=self.request.user).prefetch_related("memberships")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shelf = serializer.save(user=request.user)
        return Response(
            ShelfSerializer(shelf, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class MyShelfDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"
    lookup_url_kwarg = "shelf_slug"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ShelfCreateSerializer
        return ShelfDetailSerializer

    def get_queryset(self):
        return Shelf.objects.filter(user=self.request.user).prefetch_related(
            "memberships__book__authors"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = ShelfCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Name update does NOT regenerate slug (stable URL)
        serializer.save()
        return Response(ShelfDetailSerializer(instance, context=self.get_serializer_context()).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyShelfBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_shelf(self, request, shelf_slug):
        return get_object_or_404(Shelf, user=request.user, slug=shelf_slug)

    def post(self, request, shelf_slug, book_id):
        shelf = self._get_shelf(request, shelf_slug)
        book = get_object_or_404(Book, pk=book_id)
        _, created = ShelfMembership.objects.get_or_create(shelf=shelf, book=book)
        return Response(
            {"added": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, shelf_slug, book_id):
        shelf = self._get_shelf(request, shelf_slug)
        membership = get_object_or_404(ShelfMembership, shelf=shelf, book_id=book_id)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
