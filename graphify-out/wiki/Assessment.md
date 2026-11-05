# Assessment

> God node · 105 connections · `app/models/assessment.py`

**Community:** [Organization](Organization.md)

## Connections by Relation

### calls
- _make_assessment() `EXTRACTED`
- sync_assessments_from_firestore() `EXTRACTED`
- run_e2e_validation() `EXTRACTED`
- _make_assessment() `EXTRACTED`
- test_telemetry_roi_metrics_endpoint_with_findings() `EXTRACTED`
- run_validation() `EXTRACTED`
- .test_assessment_survives_cold_start() `EXTRACTED`
- .test_different_orgs_same_alert_id_are_independent() `EXTRACTED`
- test_calculate_ai_framework_coverage_with_data() `EXTRACTED`
- .test_full_failover_simulation() `EXTRACTED`
- .test_agentic_fix_endpoint() `EXTRACTED`
- .test_sync_finding_endpoint() `EXTRACTED`

### contains
- models/assessment.py `EXTRACTED`

### imports
- models/__init__.py `EXTRACTED`
- assessments.py `EXTRACTED`
- [organizations.py](organizations.py.md) `EXTRACTED`
- test_governance.py `EXTRACTED`
- firestore.py `EXTRACTED`
- services/assessment.py `EXTRACTED`
- drift_engine.py `EXTRACTED`
- staging_real_customer_e2e.py `EXTRACTED`
- [api/verification.py](api-verification.py.md) `EXTRACTED`
- reliability_engine.py `EXTRACTED`
- [services/integrations.py](services-integrations.py.md) `EXTRACTED`
- test_igvf.py `EXTRACTED`
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) `EXTRACTED`
- test_telemetry_verification.py `EXTRACTED`
- test_real_customer_e2e.py `EXTRACTED`
- services/organization.py `EXTRACTED`
- staging_product_integrity_validation.py `EXTRACTED`
- remediations.py `EXTRACTED`
- services/telemetry.py `EXTRACTED`
- [discovery/orchestrator.py](discovery-orchestrator.py.md) `EXTRACTED`

### inherits
- Base `EXTRACTED`

### method
- .__repr__() `EXTRACTED`

### rationale_for
- Assessment entity - represents a single readiness assessment for an… `EXTRACTED`

### uses
- [TelemetryVerificationService](TelemetryVerificationService.md) `INFERRED`
- OrganizationService `INFERRED`
- AssessmentService `INFERRED`
- [AuditCalendarService](AuditCalendarService.md) `INFERRED`
- [ContinuousScoringEngine](ContinuousScoringEngine.md) `INFERRED`
- ReportService `INFERRED`
- calculate_drift() `INFERRED`
- TechnologyDiscoveryOrchestrator `INFERRED`
- execute_simulation() `INFERRED`
- [TestAuditForecast](TestAuditForecast.md) `INFERRED`
- test_real_customer_e2e_lifecycle() `INFERRED`
- patch_remediation() `INFERRED`
- calculate_ai_framework_coverage() `INFERRED`
- create_baseline() `INFERRED`
- TestIngestionIdempotencyBarrier `INFERRED`
- _get_assessment_or_404() `INFERRED`
- process_wazuh_agent_disconnections() `INFERRED`
- calculate_sustainability_index() `INFERRED`
- list_org_remediations() `INFERRED`
- sync_finding_to_ticketing() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*