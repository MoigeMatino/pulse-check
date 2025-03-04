from fastapi import FastAPI
from app.db import init_db


def create_app() -> FastAPI:
    app = FastAPI()
    return app

app = create_app()