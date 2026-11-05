"""
Tests for Server-Side HMAC Validation and PDF Auditability.

Verifies:
- same content + same signing context -> valid signature
- modified content -> invalid signature
- missing signature -> invalid/unverified
- wrong secret -> invalid
- wrong report_id or org_id context -> invalid signature
- HMAC secret is NEVER exposed in the PDF bytes, metadata, or text
- ProfessionalPDFGenerator embeds audit traceability without secret leakage
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
import pytest

from app.reports.hmac_service import (
    compute_content_sha256,
    sign_report_content,
    verify_report_hmac,
    build_audit_metadata,
    get_hmac_secret,
)
from app.reports.pdf import ProfessionalPDFGenerator


def test_hmac_valid_signature():
    """Same content and context produce a valid HMAC signature."""
    report_id = "rep-1001"
    org_id = "org-enterprise-memorial"
    content = b"%PDF-1.4 Authoritative Executive Readiness Report Content"

    sig = sign_report_content(report_id, org_id, content)
    assert len(sig) == 64
    assert verify_report_hmac(report_id, org_id, content, sig) is True


def test_hmac_modified_content_fails():
    """Tampering with report content invalidates the HMAC signature."""
    report_id = "rep-1001"
    org_id = "org-enterprise-memorial"
    original_content = b"%PDF-1.4 Original Score 82.5%"
    tampered_content = b"%PDF-1.4 Tampered Score 99.9%"

    sig = sign_report_content(report_id, org_id, original_content)
    assert verify_report_hmac(report_id, org_id, tampered_content, sig) is False


def test_hmac_missing_signature_fails():
    """Empty or missing signature fails validation closed."""
    report_id = "rep-1001"
    org_id = "org-enterprise-memorial"
    content = b"%PDF-1.4 Some Content"

    assert verify_report_hmac(report_id, org_id, content, "") is False
    assert verify_report_hmac(report_id, org_id, content, None) is False


def test_hmac_wrong_secret_fails():
    """Verifying with a different secret fails validation."""
    report_id = "rep-1001"
    org_id = "org-enterprise-memorial"
    content = b"%PDF-1.4 Content"

    sig = sign_report_content(report_id, org_id, content, secret="secret-key-alpha")
    assert verify_report_hmac(report_id, org_id, content, sig, secret="secret-key-beta") is False


def test_hmac_wrong_context_fails():
    """Cross-tenant or cross-report replay attacks fail."""
    report_id_a = "rep-1001"
    report_id_b = "rep-9999"
    org_id_a = "org-memorial"
    org_id_b = "org-acme"
    content = b"%PDF-1.4 Replay Content"

    sig = sign_report_content(report_id_a, org_id_a, content)

    # Replaying same content under different org or report ID must fail
    assert verify_report_hmac(report_id_b, org_id_a, content, sig) is False
    assert verify_report_hmac(report_id_a, org_id_b, content, sig) is False


def test_secret_never_exposed_in_metadata():
    """Audit metadata includes signature and hash, but NEVER the HMAC secret."""
    report_id = "rep-audit-01"
    org_id = "org-audit-01"
    content = b"%PDF-1.4 Sample bytes"
    secret = "super-secret-production-signing-key-12345"

    meta = build_audit_metadata(report_id, org_id, content)

    assert secret not in str(meta)
    assert "hmac_signature" in meta
    assert "content_sha256" in meta
    assert meta["report_id"] == report_id
    assert meta["org_id"] == org_id


def test_pdf_generation_embeds_audit_section_and_no_secret():
    """PDF generator produces valid PDF bytes with audit section, without leaking HMAC secret."""
    generator = ProfessionalPDFGenerator()
    secret = get_hmac_secret()

    sample_assessment = {
        "id": "asmt-audit-test",
        "organization_id": "org-audit-test",
        "organization_name": "St. Jude Hospital",
        "answers": {},
        "findings": [],
        "overall_score": 84.0,
        "domain_scores": {"incident_response": 85.0, "backup": 80.0},
    }

    pdf_bytes = generator.generate(sample_assessment)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000

    # Secret string must NEVER appear in the PDF binary stream
    assert secret.encode("utf-8") not in pdf_bytes
    # Must contain audit and verification tokens
    assert b"Cryptographic Audit" in pdf_bytes or b"Audit" in pdf_bytes
