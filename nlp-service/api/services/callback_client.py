"""Centralised HTTP callback client for sending results back to Spring."""

import logging

import httpx

from api.config import settings

logger = logging.getLogger(__name__)


def patch_to_spring(chapter_id: int | str, endpoint: str, data: dict, *, timeout: float = 60.0) -> None:
    """PATCH a result payload back to the SpringShelf API.

    Args:
        chapter_id: Chapter identifier in the Spring backend.
        endpoint: Suffix of the callback URL, e.g. ``"analyse-result"``.
        data: JSON-serialisable payload.
        timeout: HTTP timeout in seconds.
    """
    url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/chapters/{chapter_id}/{endpoint}"
    logger.info("Sending PATCH to %s", url)
    response = httpx.patch(url, json=data, timeout=timeout)
    response.raise_for_status()
    logger.info("PATCH to %s succeeded (status %s)", url, response.status_code)
