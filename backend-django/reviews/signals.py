from django.db import transaction
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_book_avg_rating(sender, instance, **kwargs):
    from books.models import Book

    with transaction.atomic():
        # Lock the Book row to prevent concurrent read-modify-write race.
        book = Book.objects.select_for_update().get(id=instance.book_id)
        result = Review.objects.filter(book=book).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        avg = result["avg"] or 0.0
        book.avg_rating = round(avg, 2)
        book.ratings_count = result["count"]
        book.save(update_fields=["avg_rating", "ratings_count"])
