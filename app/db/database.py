from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def get_engine_args():
    """
    Get SQLAlchemy engine configuration based on database type.
    
    - SQLite: Uses check_same_thread=False for FastAPI compatibility
    - PostgreSQL: Uses connection pooling optimized for Cloud Run
    """
    db_url = settings.DATABASE_URL
    
    # SQLite configuration
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
        }
    
    # PostgreSQL configuration (Cloud SQL / standard Postgres)
    # Pool settings optimized for Cloud Run's autoscaling
    return {
        "pool_size": 5,              # Base pool size
        "max_overflow": 10,          # Allow up to 15 total connections
        "pool_timeout": 30,          # Wait 30s for connection
        "pool_recycle": 1800,        # Recycle connections after 30 min
        "pool_pre_ping": True,       # Verify connections before use
    }


engine = create_engine(
    settings.DATABASE_URL,
    **get_engine_args(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
