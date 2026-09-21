from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


database_url = settings.database_url.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
if database_url.startswith("postgresql"):
    connect_args["connect_timeout"] = 10
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    import app.models

    Base.metadata.create_all(bind=engine)
