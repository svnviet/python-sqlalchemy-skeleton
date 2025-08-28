import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)  # e.g. /Users/vietnguyen/Projects/trading
DB_FILE = os.path.join(BASE_DIR, "trading.db")

DATABASE_URL = f"sqlite:///{DB_FILE}"
print(DATABASE_URL)
# DATABASE_URL = "sqlite:///:memory:"   # for in-memory


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=True,  # log SQL (useful in dev)
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Generator:
    """Transactional scope for queries."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
