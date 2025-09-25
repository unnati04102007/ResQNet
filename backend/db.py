import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    # Prefer DATABASE_URL, fallback to POSTGRES_URL
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not url:
        # Example: postgresql+psycopg://user:pass@localhost:5432/resqnet
        raise RuntimeError("DATABASE_URL or POSTGRES_URL not configured in environment")
    normalized = url.strip()
    # Accept heroku-style postgres:// and normalize
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://"):]
    # Ensure SQLAlchemy driver is specified for psycopg3
    if normalized.startswith("postgresql://") and not normalized.startswith("postgresql+psycopg://"):
        normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)
    return normalized


engine = create_engine(_get_database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


