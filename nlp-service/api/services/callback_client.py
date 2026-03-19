"""Centralised HTTP callback client for sending results back to Spring."""

import logging

import httpx

from api.config import settings

logger = logging.getLogger(__name__)


def patch_to_spring(
    resource_id: int | str,
    endpoint: str,
    data: dict,
    *,
    resource: str = "chapters",
    timeout: float = 60.0,
) -> None:
    """PATCH a result payload back to the SpringShelf API.

    Args:
        resource_id: Identifier in the Spring backend.
        endpoint: Suffix of the callback URL, e.g. ``"analyse-result"``.
        data: JSON-serialisable payload.
        resource: API resource name (e.g. ``"chapters"`` or ``"books"``).
        timeout: HTTP timeout in seconds.
    """
    url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/{resource}/{resource_id}/{endpoint}"
    logger.info("Sending PATCH to %s", url)
    response = httpx.patch(url, json=data, timeout=timeout)
    response.raise_for_status()
    logger.info("PATCH to %s succeeded (status %s)", url, response.status_code)


async def patch_to_spring_async(
    resource_id: int | str,
    endpoint: str,
    data: dict,
    *,
    resource: str = "chapters",
    timeout: float = 60.0,
) -> None:
    url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/{resource}/{resource_id}/{endpoint}"
    logger.info("Sending async PATCH to %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, json=data, timeout=timeout)
        response.raise_for_status()
        logger.info("Async PATCH to %s succeeded (status %s)", url, response.status_code)
