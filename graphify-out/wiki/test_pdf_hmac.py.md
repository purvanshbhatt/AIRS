# test_pdf_hmac.py

> 29 nodes · cohesion 0.12

## Key Concepts

- **test_pdf_hmac.py** (16 connections) — `tests/test_pdf_hmac.py`
- **sign_report_content()** (13 connections) — `app/reports/hmac_service.py`
- **hmac_service.py** (9 connections) — `app/reports/hmac_service.py`
- **verify_report_hmac()** (9 connections) — `app/reports/hmac_service.py`
- **build_audit_metadata()** (7 connections) — `app/reports/hmac_service.py`
- **compute_content_sha256()** (5 connections) — `app/reports/hmac_service.py`
- **get_hmac_secret()** (5 connections) — `app/reports/hmac_service.py`
- **test_hmac_modified_content_fails()** (4 connections) — `tests/test_pdf_hmac.py`
- **test_hmac_valid_signature()** (4 connections) — `tests/test_pdf_hmac.py`
- **test_hmac_wrong_context_fails()** (4 connections) — `tests/test_pdf_hmac.py`
- **test_hmac_wrong_secret_fails()** (4 connections) — `tests/test_pdf_hmac.py`
- **test_pdf_generation_embeds_audit_section_and_no_secret()** (4 connections) — `tests/test_pdf_hmac.py`
- **test_hmac_missing_signature_fails()** (3 connections) — `tests/test_pdf_hmac.py`
- **test_secret_never_exposed_in_metadata()** (3 connections) — `tests/test_pdf_hmac.py`
- **datetime** (2 connections)
- **Server-Side HMAC Integrity Validation Service for ResilAI Reports. Enforces…** (1 connections) — `app/reports/hmac_service.py`
- **Retrieve the authoritative server-side HMAC secret. Priority: 1.…** (1 connections) — `app/reports/hmac_service.py`
- **Compute the SHA-256 hash of the binary content.** (1 connections) — `app/reports/hmac_service.py`
- **Generate an authoritative server-side HMAC-SHA256 signature for report content.…** (1 connections) — `app/reports/hmac_service.py`
- **Verify that a report's HMAC signature matches the content and signing context.…** (1 connections) — `app/reports/hmac_service.py`
- **Build public-safe audit traceability metadata for the report. NEVER includes…** (1 connections) — `app/reports/hmac_service.py`
- **Tests for Server-Side HMAC Validation and PDF Auditability. Verifies: - same…** (1 connections) — `tests/test_pdf_hmac.py`
- **PDF generator produces valid PDF bytes with audit section, without leaking HMAC…** (1 connections) — `tests/test_pdf_hmac.py`
- **Same content and context produce a valid HMAC signature.** (1 connections) — `tests/test_pdf_hmac.py`
- **Tampering with report content invalidates the HMAC signature.** (1 connections) — `tests/test_pdf_hmac.py`
- *... and 4 more nodes in this community*

## Relationships

- [pdf.py](pdf.py.md) (2 shared connections)
- [ProfessionalPDFGenerator](ProfessionalPDFGenerator.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [get_attr](get_attr.md) (1 shared connections)

## Source Files

- `app/reports/hmac_service.py`
- `tests/test_pdf_hmac.py`

## Audit Trail

- EXTRACTED: 56 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*