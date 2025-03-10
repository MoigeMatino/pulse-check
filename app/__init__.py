from fastapi import FastAPI
from api.v1.routes.ssl import router as ssl_router


def create_app() -> FastAPI:
    app = FastAPI()
    
    app.include_router(ssl_router, tags=["ssl"])
    return app

app = create_app()