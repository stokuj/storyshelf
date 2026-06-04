from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractYear
from django.utils import timezone

from ratings.models import Rating
from shelf.models import ShelfEntry


def build_user_stats(user) -> dict:
    """Aggregate one user's reading statistics into a plain dict.

    Pure read-only aggregation over ShelfEntry / Rating / Book. Shape matches
    UserStatsSerializer. All values are own-user only.
    """
    entries = ShelfEntry.objects.filter(user=user)

    by_status = {
        row["status"]: row["n"]
        for row in entries.values("status").annotate(n=Count("id"))
    }
    status_counts = {
        "want_to_read": by_status.get(ShelfEntry.Status.WANT_TO_READ, 0),
        "reading": by_status.get(ShelfEntry.Status.READING, 0),
        "read": by_status.get(ShelfEntry.Status.READ, 0),
    }

    read_entries = entries.filter(status=ShelfEntry.Status.READ)
    pages_read = read_entries.aggregate(s=Sum("book__page_count"))["s"] or 0

    avg = Rating.objects.filter(user=user).aggregate(a=Avg("rating"))["a"]
    avg_rating_given = round(avg, 1) if avg is not None else None

    totals = {
        "pages_read": pages_read,
        "avg_rating_given": avg_rating_given,
    }

    per_year = (
        read_entries.filter(finish_date__isnull=False)
        .annotate(year=ExtractYear("finish_date"))
        .values("year")
        .annotate(count=Count("id"))
        .order_by("year")
    )
    books_per_year = [{"year": row["year"], "count": row["count"]} for row in per_year]

    rating_map = {
        row["rating"]: row["n"]
        for row in Rating.objects.filter(user=user)
        .values("rating")
        .annotate(n=Count("id"))
    }
    rating_distribution = [
        {"rating": r, "count": rating_map.get(r, 0)} for r in range(1, 6)
    ]

    pairs = read_entries.filter(finish_date__isnull=False).values_list(
        "created_at", "finish_date"
    )
    # Only count real "on shelf" durations; a finish_date predating created_at
    # (backdated/historical) is not a meaningful duration and is excluded.
    # Normalize created_at (UTC, USE_TZ) to the app timezone so it compares
    # like-for-like with finish_date, which is written via timezone.localdate().
    deltas = []
    for created, finish in pairs:
        days = (finish - timezone.localtime(created).date()).days
        if days >= 0:
            deltas.append(days)
    time_on_shelf_days = round(sum(deltas) / len(deltas), 1) if deltas else None

    return {
        "status_counts": status_counts,
        "totals": totals,
        "books_per_year": books_per_year,
        "rating_distribution": rating_distribution,
        "time_on_shelf_days": time_on_shelf_days,
    }
