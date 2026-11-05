# TelemetryVerificationService

> God node · 65 connections · `app/services/telemetry.py`

**Community:** [TelemetryVerificationService](TelemetryVerificationService.md)

## Connections by Relation

### calls
- run_e2e_validation() `EXTRACTED`
- .broadcast_org_update() `EXTRACTED`
- .test_different_orgs_same_alert_id_are_independent() `EXTRACTED`
- .test_full_pipeline_siem_to_score() `EXTRACTED`
- .test_multiple_findings_verified_in_sequence() `EXTRACTED`
- .test_contradicted_finding_has_elevated_weight() `EXTRACTED`
- .test_soc_verified_finding_gets_full_weight() `EXTRACTED`
- .test_duplicate_alert_id_returns_already_exists() `EXTRACTED`
- .test_duplicate_does_not_create_extra_records() `EXTRACTED`
- .test_direct_finding_rule_id_match() `EXTRACTED`
- .test_nist_category_prefix_match() `EXTRACTED`
- .test_no_match_returns_no_match_status() `EXTRACTED`
- .test_splunk_source_sets_correct_verification_source() `EXTRACTED`
- .test_valid_siem_payload_creates_soc_verified_provenance() `EXTRACTED`
- .test_evidence_hash_is_deterministic() `EXTRACTED`
- .test_finding_promoted_to_soc_verified() `EXTRACTED`
- .test_provenance_record_persisted() `EXTRACTED`
- .test_duplicate_alert_returns_already_exists() `EXTRACTED`
- .test_no_duplicate_provenance_record_created() `EXTRACTED`
- .test_score_change_emits_structured_log() `EXTRACTED`

### contains
- services/telemetry.py `EXTRACTED`

### imports
- staging_real_customer_e2e.py `EXTRACTED`
- test_telemetry_verification.py `EXTRACTED`
- test_real_customer_e2e.py `EXTRACTED`
- staging_product_integrity_validation.py `EXTRACTED`
- test_governance_ingestion.py `EXTRACTED`
- v1/telemetry.py `EXTRACTED`
- governance_webhook.py `EXTRACTED`
- telemetry_roi.py `EXTRACTED`
- websocket_manager.py `EXTRACTED`

### method
- .process_siem_event() `EXTRACTED`
- ._compute_evidence_hash() `EXTRACTED`
- .recompute_ghi_for_assessment() `EXTRACTED`
- .ingest_siem_telemetry() `EXTRACTED`
- ._match_finding() `EXTRACTED`
- .calculate_roi_metrics() `EXTRACTED`
- .__init__() `EXTRACTED`
- .mark_siem_stale() `EXTRACTED`

### rationale_for
- Processes inbound SIEM events and manages FindingProvenance records. Thread-… `EXTRACTED`

### uses
- [Assessment](Assessment.md) `INFERRED`
- [Finding](Finding.md) `INFERRED`
- AssessmentStatus `INFERRED`
- FindingProvenance `INFERRED`
- [ContinuousScoringEngine](ContinuousScoringEngine.md) `INFERRED`
- ProvenanceStatus `INFERRED`
- [FrameworkMappingRegistry](FrameworkMappingRegistry.md) `INFERRED`
- TelemetryConnectionManager `INFERRED`
- test_real_customer_e2e_lifecycle() `INFERRED`
- ControlRuleRegistry `INFERRED`
- TestIngestionIdempotencyBarrier `INFERRED`
- VerificationSource `INFERRED`
- run_e2e_backend_validation() `INFERRED`
- ScoreAuditLog `INFERRED`
- TestSIEMEventProcessing `INFERRED`
- ingest_siem_event() `INFERRED`
- get_telemetry_roi_metrics() `INFERRED`
- TestGHIRecomputation `INFERRED`
- ingest_webhook_event() `INFERRED`
- TestDeterministicIngestionStateTransition `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*