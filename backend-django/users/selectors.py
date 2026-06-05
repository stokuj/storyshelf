from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import User


def public_owner_or_404(request, handle):
    """Fetch a user by handle; 404 if their profile is private to the requester.

    Shared gating for public, profile_public-bounded reads of a user's content
    (shelves, reviews, …). A private profile hides its content from everyone
    except the owner.
    """
    owner = get_object_or_404(User, handle=handle)
    if not owner.profile_public and owner != request.user:
        raise Http404("No User matches the given query.")
    return owner
