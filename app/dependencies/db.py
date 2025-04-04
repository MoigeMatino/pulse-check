from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from app.api.v1.models import NotificationPreference  # noqa: F401
from app.api.v1.models import SSLLog  # noqa: F401
from app.api.v1.models import UptimeLog  # noqa: F401
from app.api.v1.models import User  # noqa: F401
from app.api.v1.models import Website  # noqa: F401
from app.dependencies.settings import get_settings

settings = get_settings()

DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.db_host}/{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# don't need this now, alembic got it handled
# def init_db():
#     SQLModel.metadata.create_all(engine)
