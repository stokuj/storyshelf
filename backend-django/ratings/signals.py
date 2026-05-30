from django.db import transaction
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Rating


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_book_avg_rating(sender, instance, **kwargs):
    from books.models import Book

    with transaction.atomic():
        book = Book.objects.select_for_update().get(id=instance.book_id)
        agg = Rating.objects.filter(book_id=book.id).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        book.avg_rating = round(agg["avg"], 2) if agg["count"] else 0.0
        book.ratings_count = agg["count"]
        book.save(update_fields=["avg_rating", "ratings_count"])
