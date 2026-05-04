"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "postgresql://checkup:checkup@localhost:5432/checkup"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    """

    pass


def get_db():
    """
    FastAPI dependency that provides a database session.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
