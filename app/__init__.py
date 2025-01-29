from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database
    init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    return app

app = create_app()