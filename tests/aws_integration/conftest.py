import os
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from app.db.database import Base
    import app.models  # Ensure all models are registered with Base.metadata
except ImportError:
    # Fallback for scaffolding if app is not fully available
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()

@pytest.fixture
def test_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_org_id():
    return str(uuid.uuid4())

@pytest.fixture
def test_org_id_b():
    return str(uuid.uuid4())

@pytest.fixture
def aws_credentials_from_env():
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("AWS_REGION")
    
    if not (access_key and secret_key and region):
        pytest.skip("AWS credentials not found in environment variables.")
        
    return {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "aws_region": region
    }

@pytest.fixture
def mock_aws_credentials():
    return {
        "aws_access_key_id": "mock_access_key",
        "aws_secret_access_key": "mock_secret_key",
        "aws_region": "us-east-1"
    }

@pytest.fixture
def connector_id():
    return str(uuid.uuid4())

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "aws_integration: mark test to require live AWS credentials"
    )
