"""
Database setup and configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - use SQLite for now, can switch to PostgreSQL later
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iptv_content.db")

# For SQLite, we need to handle the URL format
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't need async, and we need to handle the URL
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
else:
    # For PostgreSQL or other databases
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)

