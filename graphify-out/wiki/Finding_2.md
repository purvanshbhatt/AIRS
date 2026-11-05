# Finding

> God node · 68 connections · `app/models/finding.py`

**Community:** [Organization](Organization.md)

## Connections by Relation

### calls
- _make_finding() `EXTRACTED`
- sync_assessments_from_firestore() `EXTRACTED`
- run_e2e_validation() `EXTRACTED`
- process_wazuh_agent_disconnections() `EXTRACTED`
- _make_finding() `EXTRACTED`
- generate_finding_from_cve() `EXTRACTED`
- test_telemetry_roi_metrics_endpoint_with_findings() `EXTRACTED`
- ._sync_to_legacy_tables() `EXTRACTED`
- .test_different_orgs_same_alert_id_are_independent() `EXTRACTED`
- test_calculate_ai_framework_coverage_with_data() `EXTRACTED`
- .test_agentic_fix_endpoint() `EXTRACTED`
- .test_sync_finding_endpoint() `EXTRACTED`

### contains
- finding.py `EXTRACTED`

### imports
- models/__init__.py `EXTRACTED`
- assessments.py `EXTRACTED`
- test_governance.py `EXTRACTED`
- firestore.py `EXTRACTED`
- services/assessment.py `EXTRACTED`
- drift_engine.py `EXTRACTED`
- staging_real_customer_e2e.py `EXTRACTED`
- [api/verification.py](api-verification.py.md) `EXTRACTED`
- reliability_engine.py `EXTRACTED`
- [services/integrations.py](services-integrations.py.md) `EXTRACTED`
- test_igvf.py `EXTRACTED`
- validation_engine.py `EXTRACTED`
- test_telemetry_verification.py `EXTRACTED`
- test_real_customer_e2e.py `EXTRACTED`
- staging_product_integrity_validation.py `EXTRACTED`
- remediations.py `EXTRACTED`
- services/telemetry.py `EXTRACTED`
- [discovery/orchestrator.py](discovery-orchestrator.py.md) `EXTRACTED`
- test_governance_ingestion.py `EXTRACTED`
- env.py `EXTRACTED`

### inherits
- Base `EXTRACTED`

### method
- .__repr__() `EXTRACTED`

### rationale_for
- Finding entity - represents a gap or issue identified during assessment. `EXTRACTED`

### uses
- [TelemetryVerificationService](TelemetryVerificationService.md) `INFERRED`
- AssessmentService `INFERRED`
- validate_organization() `INFERRED`
- [AuditCalendarService](AuditCalendarService.md) `INFERRED`
- [ExplanationService](ExplanationService.md) `INFERRED`
- calculate_drift() `INFERRED`
- compute_audit_readiness() `INFERRED`
- TechnologyDiscoveryOrchestrator `INFERRED`
- TestAuditReadiness `INFERRED`
- compute_score() `INFERRED`
- [TestAuditForecast](TestAuditForecast.md) `INFERRED`
- test_real_customer_e2e_lifecycle() `INFERRED`
- calculate_ai_framework_coverage() `INFERRED`
- TestIngestionIdempotencyBarrier `INFERRED`
- update_finding() `INFERRED`
- calculate_sustainability_index() `INFERRED`
- run_e2e_backend_validation() `INFERRED`
- sync_finding_to_ticketing() `INFERRED`
- TestRemediationEndpoints `INFERRED`
- run_remediation_agent() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*