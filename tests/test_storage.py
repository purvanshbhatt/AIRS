"""
Tests for the storage service (local and GCS backends).
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from app.services.storage import (
    LocalStorageBackend,
    GCSStorageBackend,
    StorageError,
    BucketNotFoundError,
    ObjectNotFoundError,
    get_storage_backend,
    generate_storage_path,
    reset_storage,
)


# =============================================================================
# Local Storage Backend Tests
# =============================================================================

class TestLocalStorageBackend:
    """Tests for local filesystem storage."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def local_storage(self, temp_storage_dir):
        """Create a local storage instance."""
        return LocalStorageBackend(base_dir=temp_storage_dir)
    
    def test_store_and_retrieve(self, local_storage):
        """Test storing and retrieving a file."""
        content = b"%PDF-1.4 test content"
        object_path = "test_report.pdf"
        
        # Store
        stored_path = local_storage.store(content, object_path)
        assert stored_path == object_path
        
        # Retrieve
        retrieved = local_storage.retrieve(object_path)
        assert retrieved == content
    
    def test_store_with_subdirectories(self, local_storage, temp_storage_dir):
        """Test storing files in nested paths."""
        content = b"%PDF-1.4 nested content"
        object_path = "reports/2025/01/test_report.pdf"
        
        stored_path = local_storage.store(content, object_path)
        assert stored_path == object_path
        
        # Verify file exists
        full_path = Path(temp_storage_dir) / object_path
        assert full_path.exists()
        assert full_path.read_bytes() == content
    
    def test_retrieve_not_found(self, local_storage):
        """Test retrieving a non-existent file."""
        with pytest.raises(ObjectNotFoundError) as exc_info:
            local_storage.retrieve("nonexistent.pdf")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_delete_existing(self, local_storage):
        """Test deleting an existing file."""
        content = b"%PDF-1.4 to delete"
        object_path = "to_delete.pdf"
        
        local_storage.store(content, object_path)
        assert local_storage.exists(object_path)
        
        result = local_storage.delete(object_path)
        assert result is True
        assert not local_storage.exists(object_path)
    
    def test_delete_nonexistent(self, local_storage):
        """Test deleting a non-existent file returns False."""
        result = local_storage.delete("nonexistent.pdf")
        assert result is False
    
    def test_exists(self, local_storage):
        """Test checking file existence."""
        content = b"%PDF-1.4 exists test"
        object_path = "exists_test.pdf"
        
        assert not local_storage.exists(object_path)
        
        local_storage.store(content, object_path)
        assert local_storage.exists(object_path)
    
    def test_get_download_url_returns_none(self, local_storage):
        """Test that local storage returns None for download URL."""
        url = local_storage.get_download_url("any_path.pdf")
        assert url is None
    
    def test_directory_creation(self, temp_storage_dir):
        """Test that storage directory is created if it doesn't exist."""
        new_dir = os.path.join(temp_storage_dir, "new_subdir")
        storage = LocalStorageBackend(base_dir=new_dir)
        
        assert Path(new_dir).exists()


# =============================================================================
# GCS Storage Backend Tests (Mocked)
# =============================================================================

class TestGCSStorageBackend:
    """Tests for GCS storage backend with mocked client."""
    
    @pytest.fixture
    def mock_storage_client(self):
        """Create mock GCS client."""
        with patch("app.services.storage.GCSStorageBackend.client", new_callable=lambda: property(lambda self: MagicMock())):
            yield
    
    @pytest.fixture
    def mock_bucket(self):
        """Create mock bucket that exists."""
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = True
        return mock_bucket
    
    def test_bucket_not_found_error(self):
        """Test that missing bucket raises BucketNotFoundError."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = False
            mock_client_instance.bucket.return_value = mock_bucket
            
            with pytest.raises(BucketNotFoundError) as exc_info:
                GCSStorageBackend(bucket_name="nonexistent-bucket")
            
            assert "nonexistent-bucket" in str(exc_info.value)
    
    def test_store_success(self):
        """Test successful storage to GCS."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_blob = MagicMock()
            mock_bucket.blob.return_value = mock_blob
            mock_client_instance.bucket.return_value = mock_bucket
            
            storage = GCSStorageBackend(bucket_name="test-bucket")
            result = storage.store(b"%PDF content", "reports/test.pdf")
            
            assert result == "reports/test.pdf"
            mock_blob.upload_from_string.assert_called_once_with(
                b"%PDF content",
                content_type="application/pdf"
            )
    
    def test_retrieve_success(self):
        """Test successful retrieval from GCS."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_blob = MagicMock()
            mock_blob.exists.return_value = True
            mock_blob.download_as_bytes.return_value = b"%PDF retrieved"
            mock_bucket.blob.return_value = mock_blob
            mock_client_instance.bucket.return_value = mock_bucket
            
            storage = GCSStorageBackend(bucket_name="test-bucket")
            content = storage.retrieve("reports/test.pdf")
            
            assert content == b"%PDF retrieved"
    
    def test_retrieve_not_found(self):
        """Test retrieval of non-existent object."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_blob = MagicMock()
            mock_blob.exists.return_value = False
            mock_bucket.blob.return_value = mock_blob
            mock_client_instance.bucket.return_value = mock_bucket
            
            storage = GCSStorageBackend(bucket_name="test-bucket")
            
            with pytest.raises(ObjectNotFoundError):
                storage.retrieve("nonexistent.pdf")
    
    def test_delete_success(self):
        """Test successful deletion from GCS."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_blob = MagicMock()
            mock_blob.exists.return_value = True
            mock_bucket.blob.return_value = mock_blob
            mock_client_instance.bucket.return_value = mock_bucket
            
            storage = GCSStorageBackend(bucket_name="test-bucket")
            result = storage.delete("reports/test.pdf")
            
            assert result is True
            mock_blob.delete.assert_called_once()
    
    def test_signed_url_generation(self):
        """Test signed URL generation."""
        with patch("google.cloud.storage.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_blob = MagicMock()
            mock_blob.exists.return_value = True
            mock_blob.generate_signed_url.return_value = "https://signed-url.example.com"
            mock_bucket.blob.return_value = mock_blob
            mock_client_instance.bucket.return_value = mock_bucket
            
            storage = GCSStorageBackend(bucket_name="test-bucket")
            url = storage.get_download_url("reports/test.pdf", expiration_minutes=30)
            
            assert url == "https://signed-url.example.com"
            mock_blob.generate_signed_url.assert_called_once()


# =============================================================================
# Storage Path Generation Tests
# =============================================================================

class TestStoragePathGeneration:
    """Tests for storage path generation utility."""
    
    def test_basic_path_generation(self):
        """Test basic path generation."""
        path = generate_storage_path("abc123-uuid", "Acme Corp")
        
        assert path.startswith("reports/")
        assert "Acme_Corp" in path
        assert "abc123" in path
        assert path.endswith(".pdf")
    
    def test_special_characters_sanitized(self):
        """Test that special characters are sanitized."""
        path = generate_storage_path("uuid-123", "Company/With:Special!Chars")
        
        # Should not contain special characters
        assert "/" not in path.split("/")[-1].replace(".pdf", "").replace("Company", "").replace("_", "")
        assert ":" not in path
        assert "!" not in path
    
    def test_long_org_name_truncated(self):
        """Test that long org names are truncated."""
        long_name = "A" * 100
        path = generate_storage_path("uuid-123", long_name)
        
        # Filename part should be reasonable length
        filename = path.split("/")[-1]
        assert len(filename) < 100


# =============================================================================
# Storage Backend Selection Tests
# =============================================================================

class TestStorageBackendSelection:
    """Tests for storage backend selection logic."""
    
    @pytest.fixture(autouse=True)
    def reset_storage_singleton(self):
        """Reset storage singleton before each test."""
        reset_storage()
        yield
        reset_storage()
    
    def test_local_storage_selected_by_default(self, monkeypatch):
        """Test that local storage is selected by default."""
        monkeypatch.setenv("REPORTS_STORAGE_MODE", "local")
        monkeypatch.setenv("LOCAL_REPORTS_DIR", "./test_reports")
        
        # Clear settings cache
        from app.core.config import get_settings
        get_settings.cache_clear()
        
        backend = get_storage_backend()
        assert isinstance(backend, LocalStorageBackend)
    
    def test_gcs_storage_requires_bucket_name(self, monkeypatch):
        """Test that GCS mode requires bucket name."""
        monkeypatch.setenv("REPORTS_STORAGE_MODE", "gcs")
        monkeypatch.delenv("GCS_BUCKET_NAME", raising=False)
        
        from app.core.config import get_settings
        get_settings.cache_clear()
        
        with pytest.raises(StorageError) as exc_info:
            get_storage_backend()
        
        assert "GCS_BUCKET_NAME" in str(exc_info.value)


# =============================================================================
# Integration Tests with Report Service (Local Storage)
# =============================================================================

class TestReportServiceStorage:
    """Integration tests for report service with storage."""
    
    @pytest.fixture
    def temp_reports_dir(self):
        """Create temp directory for reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_report_creation_stores_pdf(self, temp_reports_dir, monkeypatch):
        """Test that report creation stores PDF."""
        monkeypatch.setenv("REPORTS_STORAGE_MODE", "local")
        monkeypatch.setenv("LOCAL_REPORTS_DIR", temp_reports_dir)
        
        from app.core.config import get_settings
        get_settings.cache_clear()
        reset_storage()
        
        # Verify storage directory
        from app.services.storage import get_storage
        storage = get_storage()
        assert isinstance(storage, LocalStorageBackend)
        
        # Store a test PDF
        test_content = b"%PDF-1.4 test"
        path = storage.store(test_content, "test_report.pdf")
        
        # Verify it can be retrieved
        retrieved = storage.retrieve(path)
        assert retrieved == test_content
