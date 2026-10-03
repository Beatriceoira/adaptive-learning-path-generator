from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_pgvector_extension():
    """
    Enables the pgvector extension (idempotent). Must run before
    Base.metadata.create_all() the first time, since the knowledge_chunks
    table's embedding column depends on the `vector` type it provides.
    Requires the Postgres superuser/role to have CREATE privilege, and the
    pgvector extension to be installed on the Postgres server itself.
    """
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
