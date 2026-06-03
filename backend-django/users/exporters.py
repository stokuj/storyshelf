import io
import json
import zipfile
from datetime import date, datetime


class _DatetimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return super().default(o)


def build_user_export_zip(user):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # user.json
        user_data = {
            "id": user.id,
            "handle": user.handle,
            "display_name": user.display_name,
            "email": user.email,
            "bio": user.bio,
            "profile_public": user.profile_public,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        zf.writestr("user.json", json.dumps(user_data, indent=2, cls=_DatetimeEncoder))

        # follows.json
        following_qs = user.following_set.select_related("following").order_by("following__handle")
        follower_qs = user.follower_set.select_related("follower").order_by("follower__handle")
        follows_data = {
            "following": [
                {"id": f.id, "handle": f.following.handle, "followed_at": f.followed_at.isoformat()}
                for f in following_qs
            ],
            "followers": [
                {"id": f.id, "handle": f.follower.handle, "followed_at": f.followed_at.isoformat()}
                for f in follower_qs
            ],
        }
        zf.writestr("follows.json", json.dumps(follows_data, indent=2, cls=_DatetimeEncoder))

        # shelf_entries.json
        shelf_qs = user.shelf_entries.select_related("book").order_by("-created_at")
        shelf_data = [
            {
                "book_title": e.book.title,
                "book_slug": e.book.slug,
                "status": e.status,
                "start_date": e.start_date,
                "finish_date": e.finish_date,
                "current_page": e.current_page,
                "created_at": e.created_at,
            }
            for e in shelf_qs
        ]
        zf.writestr("shelf_entries.json", json.dumps(shelf_data, indent=2, cls=_DatetimeEncoder))

        # ratings.json
        ratings_qs = user.ratings.select_related("book").order_by("-created_at")
        ratings_data = [
            {
                "book_title": r.book.title,
                "book_slug": r.book.slug,
                "rating": r.rating,
                "created_at": r.created_at,
            }
            for r in ratings_qs
        ]
        zf.writestr("ratings.json", json.dumps(ratings_data, indent=2, cls=_DatetimeEncoder))

        # reviews.json
        reviews_qs = user.reviews.select_related("book").order_by("-created_at")
        reviews_data = [
            {
                "book_title": r.book.title,
                "book_slug": r.book.slug,
                "body": r.body,
                "created_at": r.created_at,
            }
            for r in reviews_qs
        ]
        zf.writestr("reviews.json", json.dumps(reviews_data, indent=2, cls=_DatetimeEncoder))

        # shelves.json
        shelves_qs = user.shelves.prefetch_related("memberships__book").order_by("-created_at")
        shelves_data = [
            {
                "name": s.name,
                "slug": s.slug,
                "description": s.description,
                "is_public": s.is_public,
                "created_at": s.created_at,
                "books": [m.book.slug for m in s.memberships.all()],
            }
            for s in shelves_qs
        ]
        zf.writestr("shelves.json", json.dumps(shelves_data, indent=2, cls=_DatetimeEncoder))

        # avatar
        if user.avatar and user.avatar.name:
            try:
                user.avatar.open("rb")
                zf.writestr(f"avatar_{user.avatar.name.split('/')[-1]}", user.avatar.read())
                user.avatar.close()
            except (FileNotFoundError, OSError):
                pass

        # README.txt
        readme = (
            f"StoryShelf Data Export\n"
            f"Generated: {date.today().isoformat()}\n"
            f"User: {user.handle}\n\n"
            f"Contents:\n"
            f"  user.json          — profile data\n"
            f"  follows.json       — followers and following\n"
            f"  shelf_entries.json — reading shelf (status, progress, dates)\n"
            f"  ratings.json       — book ratings\n"
            f"  reviews.json       — book reviews\n"
            f"  shelves.json       — custom shelves and their books\n"
            f"  avatar_*           — profile picture (if set)\n"
        )
        zf.writestr("README.txt", readme)

    buf.seek(0)
    return buf.read()
