from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URI, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Provides a generator function for interacting with the database session.

    This function initializes a database session for use during the lifecycle of the
    context in which it is called. It ensures that the database session is properly closed
    after its use, preventing resource leaks and guaranteeing the integrity of connections.

    :yield: A database session object for interacting with the database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()