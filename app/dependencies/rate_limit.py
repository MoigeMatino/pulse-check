# from typing import Optional

from math import ceil

from fastapi import HTTPException, Request, Response, status
from fastapi_limiter.depends import RateLimiter


async def rate_limit_callback(request: Request, response: Response, expire: int):
    """
    Custom callback when rate limit is exceeded
    :param request: The FastAPI request object
    :param response: The FastAPI response object
    :param expire: The remaining milliseconds until reset
    """
    expire_seconds = ceil(expire / 1000)

    api_key = request.headers.get("X-API-Key", "unknown")
    print(
        f"Rate limit exceeded for API key: {api_key[:8]}... Retry after {expire_seconds}s"
    )

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too Many Requests. Retry after {expire_seconds} seconds.",
        headers={"Retry-After": str(expire_seconds)},
    )


def get_api_key_rate_limiter():
    """Rate limiter that uses API key as identifier"""

    async def api_key_identifier(request: Request):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return f"ip:{request.client.host}" if request.client else "anonymous"
        return f"api_key:{api_key}"

    return RateLimiter(
        times=60,
        seconds=60,
        identifier=api_key_identifier,
        callback=rate_limit_callback,
    )
