from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware, now
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ratings.models import Rating
from reviews.models import Review
from shelf.models import ShelfEntry
from users.models import UserFollow

from .serializers import FeedItemSerializer, FeedResponseSerializer

PAGE_SIZE = 20
BODY_PREVIEW = 280


def _actor(user, request):
    avatar_url = None
    if user.avatar:
        avatar_url = (
            request.build_absolute_uri(user.avatar.url) if request else user.avatar.url
        )
    return {
        "handle": user.handle,
        "display_name": user.display_name,
        "avatar_url": avatar_url,
    }


def _book(book):
    return {"title": book.title, "slug": book.slug, "cover_url": book.cover_url}


def _rating_entry(r, request):
    return {
        "type": "rating",
        "timestamp": r.updated_at,
        "actor": _actor(r.user, request),
        "book": _book(r.book),
        "rating": r.rating,
        "body": None,
        "finish_date": None,
    }


def _review_entry(r, request):
    return {
        "type": "review",
        "timestamp": r.updated_at,
        "actor": _actor(r.user, request),
        "book": _book(r.book),
        "rating": None,
        "body": r.body[:BODY_PREVIEW],
        "finish_date": None,
    }


def _finished_entry(e, request):
    return {
        "type": "finished",
        "timestamp": e.finished_at,
        "actor": _actor(e.user, request),
        "book": _book(e.book),
        "rating": None,
        "body": None,
        "finish_date": e.finish_date,
    }


class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=FeedResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="before",
                type=str,
                required=False,
                description="ISO-8601 cursor; return activity strictly older than this.",
            )
        ],
    )
    def get(self, request):
        before_raw = request.query_params.get("before")
        before = parse_datetime(before_raw) if before_raw else now()
        if before is None:
            return Response(
                {"detail": "Invalid 'before' timestamp."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # A cursor without an offset (e.g. a hand-supplied one) parses as naive;
        # comparing it to tz-aware columns warns/misbehaves under USE_TZ.
        if is_naive(before):
            before = make_aware(before)

        # Evaluated once into an IN (...) list (reused across the three queries
        # below); profile_public gating happens here, not as a post-filter.
        following_ids = list(
            UserFollow.objects.filter(
                follower=request.user, following__profile_public=True
            ).values_list("following_id", flat=True)
        )

        ratings = (
            Rating.objects.filter(user_id__in=following_ids, updated_at__lt=before)
            .select_related("user", "book")
            .order_by("-updated_at")[:PAGE_SIZE]
        )
        reviews = (
            Review.objects.filter(user_id__in=following_ids, updated_at__lt=before)
            .select_related("user", "book")
            .order_by("-updated_at")[:PAGE_SIZE]
        )
        finished = (
            ShelfEntry.objects.filter(
                user_id__in=following_ids,
                status=ShelfEntry.Status.READ,
                finished_at__isnull=False,
                finished_at__lt=before,
            )
            .select_related("user", "book")
            .order_by("-finished_at")[:PAGE_SIZE]
        )

        items = (
            [_rating_entry(r, request) for r in ratings]
            + [_review_entry(r, request) for r in reviews]
            + [_finished_entry(e, request) for e in finished]
        )
        items.sort(key=lambda x: x["timestamp"], reverse=True)
        page = items[:PAGE_SIZE]
        # Timestamp-only cursor (strict <). Two events sharing the exact same
        # microsecond at a page boundary could be skipped — practically
        # impossible with auto_now precision per save; acceptable at this scale.
        next_before = (
            page[-1]["timestamp"].isoformat() if len(page) == PAGE_SIZE else None
        )

        return Response(
            {
                "results": FeedItemSerializer(page, many=True).data,
                "next_before": next_before,
            }
        )
