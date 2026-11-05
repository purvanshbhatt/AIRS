from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

SENTINEL_DATABASE_URL = os.environ.get("SENTINEL_DATABASE_URL", "sqlite:///./sentinel_dev.db")

engine = create_engine(
    SENTINEL_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SENTINEL_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_sentinel_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
