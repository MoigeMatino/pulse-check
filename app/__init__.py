# from contextlib import asynccontextmanager

# import redis
from fastapi import FastAPI

from .api.v1.routes.auth import router as auth_router
from .api.v1.routes.ssl import router as ssl_router
from .api.v1.routes.website import router as website_router

# from fastapi_limiter import FastAPILimiter  # noqa: F401
# from fastapi_limiter.depends import RateLimiter


REDIS_URL = "redis://127.0.0.1:6379"


# @asynccontextmanager
# async def lifespan(_: FastAPI):
#     redis_connection = redis.from_url(REDIS_URL, encoding="utf8")
#     await FastAPILimiter.init(
#         redis=redis_connection,
#         identifier=service_name_identifier, # noqa: F821
#         http_callback=custom_callback,  # noqa: F821
#     )
#     yield
#     await FastAPILimiter.close()


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(ssl_router, tags=["ssl"])
    app.include_router(website_router, tags=["websites"])
    app.include_router(auth_router, tags=["auth"])
    return app


app = create_app()
