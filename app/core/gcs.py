"""
Google Cloud Storage integration for AIRS.
Handles uploading PDFs and generating short-lived signed URLs for secure,
tenant-isolated downloads.
"""
import logging
from datetime import timedelta
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("airs.gcs")

try:
    from google.cloud import storage
except ImportError:
    storage = None

def upload_and_sign_pdf(pdf_bytes: bytes, filename: str) -> Optional[str]:
    """
    Uploads a PDF byte buffer to the configured GCS bucket and returns a signed URL
    valid for 15 minutes.
    
    If running locally without GCP credentials, returns a mock URL.
    """
    project_id = getattr(settings, "GCP_PROJECT_ID", None)
    bucket_name = f"{project_id}-reports" if project_id else "mock-airs-reports-bucket"
    
    if not storage or not project_id or getattr(settings, "DEBUG", False):
        logger.warning("GCS upload bypassed (No project ID or DEBUG=True). Returning mock signed URL.")
        return f"https://storage.googleapis.com/{bucket_name}/{filename}?signed=mock"
        
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # Upload
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")
        logger.info(f"Successfully uploaded {filename} to GCS bucket {bucket_name}")
        
        # Generate signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="GET",
        )
        return signed_url
    except Exception as exc:
        logger.error(f"Failed to upload to GCS and generate signed URL: {exc}")
        return None
