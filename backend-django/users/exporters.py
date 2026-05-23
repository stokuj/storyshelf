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
            "handle": user.handle,
            "display_name": user.display_name,
            "email": user.email,
            "bio": user.bio,
            "profile_public": user.profile_public,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        zf.writestr("user.json", json.dumps(user_data, indent=2))

        # shelf_entries.json
        entries = list(
            user.shelf_entries.select_related("book").order_by("-created_at")
        )
        shelf_entries_data = [
            {
                "book_id": e.book_id,
                "book_title": e.book.title,
                "status": e.status,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "finish_date": e.finish_date.isoformat() if e.finish_date else None,
                "personal_rating": e.personal_rating,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
        zf.writestr(
            "shelf_entries.json",
            json.dumps(shelf_entries_data, indent=2, cls=_DatetimeEncoder),
        )

        # reviews.json
        reviews = list(
            user.review_set.select_related("book").order_by("-created_at")
        )
        reviews_data = [
            {
                "book_id": r.book_id,
                "book_title": r.book.title,
                "rating": r.rating,
                "content": r.content,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ]
        zf.writestr("reviews.json", json.dumps(reviews_data, indent=2, cls=_DatetimeEncoder))

        # follows.json
        following_qs = user.following_set.select_related("following").order_by("following__handle")
        follower_qs = user.follower_set.select_related("follower").order_by("follower__handle")
        follows_data = {
            "following": [f.following.handle for f in following_qs],
            "followers": [f.follower.handle for f in follower_qs],
        }
        zf.writestr("follows.json", json.dumps(follows_data, indent=2))

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
            f"  user.json         — profile data\n"
            f"  shelf_entries.json — reading history\n"
            f"  reviews.json      — book reviews\n"
            f"  follows.json       — followers and following\n"
            f"  avatar_*          — profile picture (if set)\n"
        )
        zf.writestr("README.txt", readme)

    buf.seek(0)
    return buf.read()
