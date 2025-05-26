from fastapi import FastAPI

from .api.v1.routes.auth import router as auth_router
from .api.v1.routes.ssl import router as ssl_router
from .api.v1.routes.website import router as website_router


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(ssl_router, tags=["ssl"])
    app.include_router(website_router, tags=["websites"])
    app.include_router(auth_router, tags=["auth"])
    return app


app = create_app()
