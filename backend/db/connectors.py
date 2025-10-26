"""
Database connection management for the Opera Research platform.

Provides SQLAlchemy engine and session management for:
- FastAPI endpoints
- ETL pipeline scripts
- Jupyter notebooks

Compatible with:
- Local PostgreSQL
- Neon (serverless Postgres)
- Supabase
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/opera_research")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """Get the SQLAlchemy engine for direct connections."""
    return engine


def test_connection():
    """
    Test database connection.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print(f"✅ Database connection successful: {DATABASE_URL}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# Connection pool stats
def get_pool_status():
    """Get connection pool statistics."""
    return {
        "pool_size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
    }


if __name__ == "__main__":
    # Test connection when run directly
    print("Testing database connection...")
    test_connection()
    print(f"\nPool status: {get_pool_status()}")
