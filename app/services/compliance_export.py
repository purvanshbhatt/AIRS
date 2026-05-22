"""
Service for exporting compliance reports to Google Cloud Storage.
"""
import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
import logging

from google.cloud import storage
from app.db.database import SessionLocal
from app.services.assessment import AssessmentService
from app.reports.pdf import ProfessionalPDFGenerator

logger = logging.getLogger(__name__)

def export_compliance_report_to_gcs(assessment_id: str, owner_uid: str) -> None:
    """
    Background task to generate a compliance PDF report, cryptographically sign it,
    and automatically push it to a secure GCS bucket.
    """
    db = SessionLocal()
    try:
        assessment_service = AssessmentService(db, owner_uid)
        assessment = assessment_service.get(assessment_id)
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found for export.")
            return
            
        summary = assessment_service.get_summary(assessment_id)
        if not summary:
            logger.error(f"Could not generate summary for assessment {assessment_id}.")
            return
            
        # Generate PDF without LLM usage
        pdf_generator = ProfessionalPDFGenerator()
        pdf_bytes = pdf_generator.generate(summary)
        
        # Timestamp the report
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Cryptographically sign the report using HMAC-SHA256
        secret_key = os.getenv("COMPLIANCE_SIGNING_KEY", "default-insecure-key").encode('utf-8')
        signature = hmac.new(secret_key, pdf_bytes, hashlib.sha256).hexdigest()
        
        # Prepare metadata
        metadata = {
            "assessment_id": assessment_id,
            "organization_id": assessment.organization_id,
            "timestamp": timestamp,
            "signature": signature,
            "algorithm": "HMAC-SHA256",
            "score": summary.get("overall_score"),
        }
        
        # Upload to GCS
        bucket_name = os.getenv("COMPLIANCE_GCS_BUCKET", "resilai-audit-ledgers-staging")
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            # Use UTC date for path
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            base_path = f"reports/{assessment.organization_id}/{assessment_id}/{date_str}"
            
            # Upload PDF
            pdf_blob_name = f"{base_path}/compliance_report.pdf"
            pdf_blob = bucket.blob(pdf_blob_name)
            pdf_blob.upload_from_string(pdf_bytes, content_type="application/pdf")
            
            # Upload Metadata
            meta_blob_name = f"{base_path}/metadata.json"
            meta_blob = bucket.blob(meta_blob_name)
            meta_blob.upload_from_string(json.dumps(metadata), content_type="application/json")
            
            logger.info(f"Successfully exported compliance report for {assessment_id} to {bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to upload compliance export to GCS: {e}")
            
    finally:
        db.close()
