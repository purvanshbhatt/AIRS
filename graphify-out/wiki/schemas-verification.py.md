# schemas/verification.py

> 22 nodes · cohesion 0.12

## Key Concepts

- **schemas/verification.py** (17 connections) — `app/schemas/verification.py`
- **VerificationResultSchema** (12 connections) — `app/schemas/verification.py`
- **services/verification.py** (12 connections) — `app/services/verification.py`
- **VerificationStatusEnum** (6 connections) — `app/schemas/verification.py`
- **.generate_audit_trail()** (6 connections) — `app/services/verification.py`
- **AuditTrailFindingSchema** (5 connections) — `app/schemas/verification.py`
- **AuditTrailSchema** (5 connections) — `app/schemas/verification.py`
- **MTTRExecutiveSummarySchema** (4 connections) — `app/schemas/verification.py`
- **MTTRChartDataPoint** (3 connections) — `app/schemas/verification.py`
- **MTTRMetadata** (3 connections) — `app/schemas/verification.py`
- **Enum** (2 connections)
- **str** (1 connections)
- **Pydantic schemas for the Verification & Audit Trail API. Defines…** (1 connections) — `app/schemas/verification.py`
- **Single data point for the Executive Risk-Reduction Recharts graph.** (1 connections) — `app/schemas/verification.py`
- **Deterministic metadata backing the MTTR summary.** (1 connections) — `app/schemas/verification.py`
- **Board-ready MTTR + risk-reduction executive summary.** (1 connections) — `app/schemas/verification.py`
- **Badge status for a finding after SIEM cross-reference.** (1 connections) — `app/schemas/verification.py`
- **Result of cross-referencing a single finding against SIEM logs.** (1 connections) — `app/schemas/verification.py`
- **Compact finding representation inside the audit trail.** (1 connections) — `app/schemas/verification.py`
- **Tamper-evident audit trail for an assessment's scoring + verification.** (1 connections) — `app/schemas/verification.py`
- **VerificationService — SIEM-Corroborated Finding Verification. Cross-references…** (1 connections) — `app/services/verification.py`
- **Generate a tamper-evident JSON audit trail. The integrity_hash is a SHA-256 of…** (1 connections) — `app/services/verification.py`

## Relationships

- [VerificationService](VerificationService.md) (9 shared connections)
- [api/verification.py](api-verification.py.md) (8 shared connections)
- [BaseModel](BaseModel.md) (6 shared connections)
- [liability_roi.py](liability_roi.py.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [EvidenceLedger](EvidenceLedger.md) (1 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (1 shared connections)
- [test_microsoft_connector.py](test_microsoft_connector.py.md) (1 shared connections)

## Source Files

- `app/schemas/verification.py`
- `app/services/verification.py`

## Audit Trail

- EXTRACTED: 58 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*