import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from .api.v1.routes.auth import router as auth_router
from .api.v1.routes.ssl import router as ssl_router
from .api.v1.routes.website import router as website_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_limiter():
    """Initialize the FastAPI rate limiter with Redis"""
    try:
        redis_instance = redis.from_url("redis://redis:6379/0")
        await FastAPILimiter.init(redis_instance)
        logger.info("Redis connection established for rate limiting")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up...")
    try:
        await init_limiter()
        logger.info("✅ Rate limiter initialized")
        # May need to add other startup tasks here when needed
        # await init_database()
        # await init_background_tasks()

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise  # prevent the app from starting

    yield  # app runs

    # Shutdown
    logger.info("🛑 Shutting down...")

    try:
        # Shutdown tasks
        await FastAPILimiter.close()
        # Add the cleanup tasks here when needed
        # await close_database()
        # await cleanup_background_tasks()
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
        # no need to raise - app is shutting down anyway


def create_app(lifespan_manager) -> FastAPI:
    app = FastAPI(
        title="PulseCheck API",
        description="API for SSL certificate monitoring and website uptime checks",
        version="1.0.0",
        lifespan=lifespan_manager,
    )

    app.include_router(ssl_router, tags=["ssl"])
    app.include_router(website_router, tags=["websites"])
    app.include_router(auth_router, tags=["auth"])
    return app


app = create_app(lifespan)
