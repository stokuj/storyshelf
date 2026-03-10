import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_key(request) -> str:
    test_id = os.getenv("PYTEST_CURRENT_TEST")
    if test_id:
        return f"{get_remote_address(request)}:{test_id}"
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)
