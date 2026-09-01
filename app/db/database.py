from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


import os
from sqlalchemy.pool import StaticPool

def get_engine_args():
    """
    Get SQLAlchemy engine configuration based on database type.
    
    - SQLite: Uses check_same_thread=False for FastAPI compatibility
    - PostgreSQL: Uses connection pooling optimized for Cloud Run
    """
    db_url = settings.DATABASE_URL
    
    # SQLite configuration
    if db_url.startswith("sqlite"):
        args = {"connect_args": {"check_same_thread": False}}
        if db_url == "sqlite://" or db_url == "sqlite:///:memory:" or os.environ.get("TESTING") == "true":
            args["poolclass"] = StaticPool
        return args
    
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

# Optional Read Replica Support
replica_engine = None
if hasattr(settings, "DATABASE_REPLICA_URL") and settings.DATABASE_REPLICA_URL:
    replica_engine = create_engine(
        settings.DATABASE_REPLICA_URL,
        **get_engine_args(),
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if replica_engine:
    ReplicaSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=replica_engine)
else:
    # Fallback to primary if no replica is configured
    ReplicaSessionLocal = SessionLocal

Base = declarative_base()


def get_db():
    """Dependency to get primary database session (Read/Write)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_replica_db():
    """Dependency to get replica database session (Read-Only)."""
    db = ReplicaSessionLocal()
    try:
        yield db
    finally:
        db.close()
