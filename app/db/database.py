from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings


def get_engine_args():
    """
    Get SQLAlchemy engine configuration based on database type.
    
    - SQLite: Uses check_same_thread=False for FastAPI compatibility
    - PostgreSQL: Uses NullPool for Cloud Run (better for serverless)
    """
    db_url = settings.DATABASE_URL
    
    # SQLite configuration
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
        }
    
    # PostgreSQL configuration (Cloud SQL / standard Postgres)
    # For Cloud Run / serverless: NullPool creates fresh connections each request
    # This avoids stale connection issues at the cost of slightly more latency
    if settings.is_prod:
        return {
            "poolclass": NullPool,  # No pooling - fresh connections each time
        }
    
    # For local development, use QueuePool with aggressive recycling
    return {
        "poolclass": QueuePool,
        "pool_size": 5,              # Base pool size
        "max_overflow": 10,          # Allow up to 15 total connections
        "pool_timeout": 30,          # Wait 30s for connection
        "pool_recycle": 300,         # Recycle connections after 5 min
        "pool_pre_ping": True,       # Verify connections before use
    }


engine = create_engine(
    settings.DATABASE_URL,
    **get_engine_args(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency to get database session.
    
    Creates a new session for each request and ensures it's properly closed.
    Handles rollback on exceptions to avoid connection state issues.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback on any exception to ensure connection is in clean state
        db.rollback()
        raise
    finally:
        db.close()
