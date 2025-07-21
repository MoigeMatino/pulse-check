# from typing import Optional

import redis.asyncio as redis

# from fastapi import Depends, HTTPException, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


async def init_limiter():
    redis_instance = redis.from_url(
        "redis://redis:6379/0"
    )  # references container redis
    await FastAPILimiter.init(redis_instance)


def get_api_key_rate_limiter():
    # to use X-API-Key header for rate limiting ie. limiting per api key
    return RateLimiter(times=60, seconds=60)
