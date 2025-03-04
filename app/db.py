from sqlmodel import Session, SQLModel, create_engine

from app.dependencies import get_settings
from app.core.models import * # noqa: F401

settings = get_settings()

DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.db_host}/{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL, echo=True)

# don't need this now, alembic got it handled
# def init_db():
#     SQLModel.metadata.create_all(engine)