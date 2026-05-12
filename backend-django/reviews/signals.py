from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_book_avg_rating(sender, instance, **kwargs):
    from books.models import Book

    result = Review.objects.filter(book=instance.book).aggregate(avg=Avg("rating"))
    avg = result["avg"] or 0.0
    count = Review.objects.filter(book=instance.book).count()
    Book.objects.filter(id=instance.book_id).update(
        avg_rating=round(avg, 2), ratings_count=count
    )
