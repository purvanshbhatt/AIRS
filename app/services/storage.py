"""
Report storage service with local and GCS backends.

Provides a unified interface for storing and retrieving PDF reports.
- Local mode: Stores files in ./generated_reports/ directory
- GCS mode: Stores files in a Google Cloud Storage bucket with signed URLs

Security:
- GCS bucket should NOT be public
- Access is controlled via Cloud Run service account
- Download uses short-lived signed URLs (15 min default)
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class BucketNotFoundError(StorageError):
    """Raised when GCS bucket does not exist or is not accessible."""
    pass


class ObjectNotFoundError(StorageError):
    """Raised when stored object is not found."""
    pass


class BaseStorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def store(self, content: bytes, object_path: str) -> str:
        """
        Store PDF content.
        
        Args:
            content: PDF file bytes
            object_path: Storage path/key for the file
            
        Returns:
            Storage path that can be used to retrieve the file
            
        Raises:
            StorageError: If storage fails
        """
        pass
    
    @abstractmethod
    def retrieve(self, object_path: str) -> bytes:
        """
        Retrieve PDF content.
        
        Args:
            object_path: Storage path/key for the file
            
        Returns:
            PDF file bytes
            
        Raises:
            ObjectNotFoundError: If file is not found
            StorageError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def delete(self, object_path: str) -> bool:
        """
        Delete stored PDF.
        
        Args:
            object_path: Storage path/key for the file
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def get_download_url(self, object_path: str, expiration_minutes: int = 15) -> Optional[str]:
        """
        Get a download URL for the file.
        
        For GCS, returns a signed URL.
        For local, returns None (use retrieve() instead).
        
        Args:
            object_path: Storage path/key for the file
            expiration_minutes: URL expiration time
            
        Returns:
            Download URL or None if not supported
        """
        pass
    
    @abstractmethod
    def exists(self, object_path: str) -> bool:
        """Check if file exists at path."""
        pass


class LocalStorageBackend(BaseStorageBackend):
    """
    Local file system storage backend.
    
    Stores files in a local directory, suitable for development.
    """
    
    def __init__(self, base_dir: str = "./generated_reports"):
        """
        Initialize local storage.
        
        Args:
            base_dir: Base directory for storing files
        """
        self.base_dir = Path(base_dir)
        self._ensure_dir_exists()
    
    def _ensure_dir_exists(self):
        """Create base directory if it doesn't exist."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage directory: {self.base_dir.absolute()}")
        except OSError as e:
            raise StorageError(f"Failed to create storage directory: {e}")
    
    def _get_full_path(self, object_path: str) -> Path:
        """Get full file path from object path."""
        # Ensure path is safe (no directory traversal)
        safe_path = Path(object_path).name if "/" not in object_path else object_path
        return self.base_dir / safe_path
    
    def store(self, content: bytes, object_path: str) -> str:
        """Store PDF to local filesystem."""
        try:
            file_path = self._get_full_path(object_path)
            # Ensure subdirectories exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            logger.info(f"Stored PDF locally: {file_path}")
            return str(object_path)
        except OSError as e:
            raise StorageError(f"Failed to store PDF locally: {e}")
    
    def retrieve(self, object_path: str) -> bytes:
        """Retrieve PDF from local filesystem."""
        file_path = self._get_full_path(object_path)
        if not file_path.exists():
            raise ObjectNotFoundError(f"File not found: {object_path}")
        try:
            return file_path.read_bytes()
        except OSError as e:
            raise StorageError(f"Failed to read PDF: {e}")
    
    def delete(self, object_path: str) -> bool:
        """Delete PDF from local filesystem."""
        file_path = self._get_full_path(object_path)
        if not file_path.exists():
            return False
        try:
            file_path.unlink()
            logger.info(f"Deleted local PDF: {file_path}")
            return True
        except OSError as e:
            logger.warning(f"Failed to delete file {object_path}: {e}")
            return False
    
    def get_download_url(self, object_path: str, expiration_minutes: int = 15) -> Optional[str]:
        """Local storage doesn't support signed URLs."""
        return None
    
    def exists(self, object_path: str) -> bool:
        """Check if file exists locally."""
        return self._get_full_path(object_path).exists()


class GCSStorageBackend(BaseStorageBackend):
    """
    Google Cloud Storage backend.
    
    Stores files in a private GCS bucket with controlled access.
    Uses signed URLs for secure downloads.
    """
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize GCS storage.
        
        Args:
            bucket_name: GCS bucket name
            project_id: GCP project ID (optional, uses default if not provided)
            
        Raises:
            BucketNotFoundError: If bucket doesn't exist or not accessible
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client = None
        self._bucket = None
        self._validate_bucket()
    
    @property
    def client(self):
        """Lazy-load storage client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=self.project_id)
            except Exception as e:
                raise StorageError(f"Failed to initialize GCS client: {e}")
        return self._client
    
    @property
    def bucket(self):
        """Get bucket reference."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket
    
    def _validate_bucket(self):
        """Verify bucket exists and is accessible."""
        try:
            if not self.bucket.exists():
                raise BucketNotFoundError(
                    f"GCS bucket '{self.bucket_name}' does not exist. "
                    f"Create it with: gsutil mb gs://{self.bucket_name}"
                )
            logger.info(f"GCS storage bucket verified: gs://{self.bucket_name}")
        except BucketNotFoundError:
            raise
        except Exception as e:
            raise BucketNotFoundError(
                f"Cannot access GCS bucket '{self.bucket_name}': {e}. "
                f"Ensure the service account has Storage Object Admin role."
            )
    
    def store(self, content: bytes, object_path: str) -> str:
        """Store PDF to GCS bucket."""
        try:
            blob = self.bucket.blob(object_path)
            blob.upload_from_string(
                content,
                content_type="application/pdf"
            )
            logger.info(f"Stored PDF to GCS: gs://{self.bucket_name}/{object_path}")
            return object_path
        except Exception as e:
            raise StorageError(f"Failed to upload PDF to GCS: {e}")
    
    def retrieve(self, object_path: str) -> bytes:
        """Retrieve PDF from GCS bucket."""
        try:
            blob = self.bucket.blob(object_path)
            if not blob.exists():
                raise ObjectNotFoundError(f"Object not found: gs://{self.bucket_name}/{object_path}")
            return blob.download_as_bytes()
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to download PDF from GCS: {e}")
    
    def delete(self, object_path: str) -> bool:
        """Delete PDF from GCS bucket."""
        try:
            blob = self.bucket.blob(object_path)
            if not blob.exists():
                return False
            blob.delete()
            logger.info(f"Deleted GCS object: gs://{self.bucket_name}/{object_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete GCS object {object_path}: {e}")
            return False
    
    def get_download_url(self, object_path: str, expiration_minutes: int = 15) -> Optional[str]:
        """
        Generate a signed URL for downloading the PDF.
        
        Args:
            object_path: Storage path/key for the file
            expiration_minutes: URL validity duration (default 15 minutes)
            
        Returns:
            Signed download URL
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
        """
        try:
            blob = self.bucket.blob(object_path)
            if not blob.exists():
                raise ObjectNotFoundError(f"Object not found: gs://{self.bucket_name}/{object_path}")
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET",
                response_disposition="attachment",
            )
            logger.debug(f"Generated signed URL for {object_path} (expires in {expiration_minutes}m)")
            return url
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL: {e}")
    
    def exists(self, object_path: str) -> bool:
        """Check if object exists in GCS."""
        try:
            blob = self.bucket.blob(object_path)
            return blob.exists()
        except Exception:
            return False


def get_storage_backend() -> BaseStorageBackend:
    """
    Get configured storage backend based on settings.
    
    Returns:
        Storage backend instance (Local or GCS)
        
    Raises:
        StorageError: If configuration is invalid
        BucketNotFoundError: If GCS bucket is missing
    """
    settings = get_settings()
    
    if settings.is_gcs_storage:
        if not settings.GCS_BUCKET_NAME:
            raise StorageError("GCS_BUCKET_NAME is required when REPORTS_STORAGE_MODE=gcs")
        return GCSStorageBackend(
            bucket_name=settings.GCS_BUCKET_NAME,
            project_id=settings.GCP_PROJECT_ID
        )
    else:
        return LocalStorageBackend(base_dir=settings.LOCAL_REPORTS_DIR)


def generate_storage_path(report_id: str, org_name: str) -> str:
    """
    Generate a consistent storage path for a report PDF.
    
    Format: reports/{year}/{month}/{org_name_sanitized}_{report_id}.pdf
    
    Args:
        report_id: Report UUID
        org_name: Organization name
        
    Returns:
        Storage path string
    """
    # Sanitize org name for path safety
    safe_org = "".join(c if c.isalnum() or c in "-_" else "_" for c in org_name)[:50]
    now = datetime.utcnow()
    return f"reports/{now.year}/{now.month:02d}/{safe_org}_{report_id[:8]}.pdf"


# Module-level storage instance (lazy-loaded)
_storage_backend: Optional[BaseStorageBackend] = None


def get_storage() -> BaseStorageBackend:
    """
    Get or create the storage backend singleton.
    
    This allows for lazy initialization and caching.
    """
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = get_storage_backend()
    return _storage_backend


def reset_storage():
    """Reset storage backend (useful for testing)."""
    global _storage_backend
    _storage_backend = None
