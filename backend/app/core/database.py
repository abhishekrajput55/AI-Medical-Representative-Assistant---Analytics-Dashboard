"""
Database connection setup.

Analogy: this file is the "phone line" between our Python code
and the PostgreSQL pantry. Every other file that needs to talk
to the database borrows this connection instead of making its own.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# The "engine" manages the actual connection pool to PostgreSQL.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory that hands out "conversations" (sessions)
# with the database. Each API request gets its own session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Every model (User, Doctor, Product...) inherits from this."""
    pass


def get_db():
    """
    FastAPI dependency: gives each request a fresh database session
    and guarantees it's closed afterward, even if an error happens.
    This pattern is called a 'context manager' — like borrowing a
    library book and always returning it, even if you drop it.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
