# api/verification.py

> 27 nodes · cohesion 0.17

## Key Concepts

- **api/verification.py** (44 connections) — `app/api/verification.py`
- **get_audit_trail()** (13 connections) — `app/api/verification.py`
- **verify_assessment()** (13 connections) — `app/api/verification.py`
- **_get_assessment_or_404()** (12 connections) — `app/api/verification.py`
- **calculate_assessment_roi()** (11 connections) — `app/api/verification.py`
- **generate_forensic_trail()** (11 connections) — `app/api/verification.py`
- **get_finding_verification_status()** (11 connections) — `app/api/verification.py`
- **_reconstruct_answers()** (9 connections) — `app/api/verification.py`
- **get_mttr_summary()** (7 connections) — `app/api/verification.py`
- **Session** (7 connections)
- **User** (7 connections)
- **_build_siem_clients()** (6 connections) — `app/api/verification.py`
- **AuditTrailResponse** (5 connections) — `app/schemas/verification.py`
- **VerifiedFindingSchema** (5 connections) — `app/schemas/verification.py`
- **VerifyAssessmentResponse** (5 connections) — `app/schemas/verification.py`
- **ForensicTrailRequest** (4 connections) — `app/api/verification.py`
- **get** (3 connections)
- **post** (3 connections)
- **Assessment** (2 connections)
- **Verification & Audit Trail API — SIEM-corroborated finding verification.…** (1 connections) — `app/api/verification.py`
- **Reconstruct the answers dict from an assessment's stored answers.** (1 connections) — `app/api/verification.py`
- **Request body for forensic trail generation.** (1 connections) — `app/api/verification.py`
- **Fetch assessment with ownership check.** (1 connections) — `app/api/verification.py`
- **Attempt to build SIEM clients from environment config. Returns…** (1 connections) — `app/api/verification.py`
- **Response for POST /verification/assess/{id}/verify** (1 connections) — `app/schemas/verification.py`
- *... and 2 more nodes in this community*

## Relationships

- [User](User.md) (8 shared connections)
- [Organization](Organization.md) (8 shared connections)
- [schemas/verification.py](schemas-verification.py.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [calculate_scores](calculate_scores.md) (7 shared connections)
- [FindingsEngine](FindingsEngine.md) (6 shared connections)
- [liability_roi.py](liability_roi.py.md) (5 shared connections)
- [VerificationService](VerificationService.md) (4 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [get_forensic_trail_agent](get_forensic_trail_agent.md) (2 shared connections)
- [mttr_analyst.py](mttr_analyst.py.md) (2 shared connections)
- [WazuhConfig](WazuhConfig.md) (2 shared connections)

## Source Files

- `app/api/verification.py`
- `app/schemas/verification.py`

## Audit Trail

- EXTRACTED: 109 (87%)
- INFERRED: 17 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*