# User

> God node · 265 connections · `app/core/auth.py`

**Community:** [User](User.md)

## Connections by Relation

### calls
- require_auth() `EXTRACTED`
- get_current_user() `EXTRACTED`
- .test_cross_org_access_denied_when_auth_required() `EXTRACTED`
- .test_own_org_access_allowed_when_auth_required() `EXTRACTED`
- .test_user_class_has_uid() `EXTRACTED`

### contains
- auth.py `EXTRACTED`

### imports
- assessments.py `EXTRACTED`
- [organizations.py](organizations.py.md) `EXTRACTED`
- [api/integrations.py](api-integrations.py.md) `EXTRACTED`
- v1/integrations.py `EXTRACTED`
- [connectors.py](connectors.py.md) `EXTRACTED`
- [api/verification.py](api-verification.py.md) `EXTRACTED`
- api/reliability.py `EXTRACTED`
- governance.py `EXTRACTED`
- [router.py](router.py.md) `EXTRACTED`
- [inventory.py](inventory.py.md) `EXTRACTED`
- drift.py `EXTRACTED`
- [policies.py](policies.py.md) `EXTRACTED`
- [v1/readiness.py](v1-readiness.py.md) `EXTRACTED`
- narratives.py `EXTRACTED`
- remediations.py `EXTRACTED`
- api/reports.py `EXTRACTED`
- api/audit_calendar.py `EXTRACTED`
- [telemetry_events.py](telemetry_events.py.md) `EXTRACTED`
- api/auditor_view.py `EXTRACTED`
- api/tech_stack.py `EXTRACTED`

### method
- .__init__() `EXTRACTED`
- .__repr__() `EXTRACTED`

### rationale_for
- Simple user model for auth context. `EXTRACTED`

### references
- get_user_org_id() `EXTRACTED`
- require_org_admin() `EXTRACTED`

### uses
- make_auth_override() `INFERRED`
- get_assessment_service() `INFERRED`
- get_org_service() `INFERRED`
- generate_narratives() `INFERRED`
- _get_org_id() `INFERRED`
- configure_wazuh() `INFERRED`
- _get_org() `INFERRED`
- run_splunk_query() `INFERRED`
- compute_score() `INFERRED`
- get_clinic_readiness() `INFERRED`
- _get_org() `INFERRED`
- _get_org() `INFERRED`
- check_splunk_logging_health() `INFERRED`
- configure_wazuh() `INFERRED`
- configure_splunk_hec() `INFERRED`
- run_logic_firewall_simulation() `INFERRED`
- get_onboarding_status() `INFERRED`
- patch_remediation() `INFERRED`
- configure_splunk() `INFERRED`
- get_siem_integration_status() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*