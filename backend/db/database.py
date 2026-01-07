"""
Database Connection and Session Management
- SQLite database connection
- Session management
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database file path (data folder in project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "ranking_history.db"

# Create data folder if not exists
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine (SQLite requires check_same_thread=False)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # SQL logging (set True for debugging)
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Initializes database tables by creating all defined models.
# @return: None
# Note: Uses SQLAlchemy Base.metadata to create tables if they don't exist.
def init_db():
    from .models import Base

    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DB_PATH}")


# Returns a database session as a context manager for dependency injection.
# @return: Generator yielding SQLAlchemy Session object
# Note: Automatically closes the session after use.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Returns a database session directly for manual management.
# @return: SQLAlchemy Session object
# Note: Caller is responsible for closing the session.
def get_session():
    return SessionLocal()
