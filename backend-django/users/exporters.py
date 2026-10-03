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
            f"  user.json — profile data\n"
            f"  avatar_*  — profile picture (if set)\n"
        )
        zf.writestr("README.txt", readme)

    buf.seek(0)
    return buf.read()
