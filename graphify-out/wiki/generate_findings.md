# generate_findings

> 67 nodes · cohesion 0.04

## Key Concepts

- **generate_findings()** (37 connections) — `app/services/findings.py`
- **Severity** (15 connections) — `app/services/findings.py`
- **TestResilienceRules** (8 connections) — `tests/test_findings.py`
- **TestDetectionCoverageRules** (7 connections) — `tests/test_findings.py`
- **TestIdentityVisibilityRules** (7 connections) — `tests/test_findings.py`
- **TestIRProcessRules** (7 connections) — `tests/test_findings.py`
- **TestTelemetryLoggingRules** (7 connections) — `tests/test_findings.py`
- **TestAggregateRules** (5 connections) — `tests/test_findings.py`
- **.test_low_identity_score_triggers_critical()** (4 connections) — `tests/test_findings.py`
- **.test_low_telemetry_score_triggers_finding()** (4 connections) — `tests/test_findings.py`
- **TestFindingsSorting** (4 connections) — `tests/test_findings.py`
- **.test_critical_edr_coverage_triggers_critical()** (3 connections) — `tests/test_findings.py`
- **.test_good_edr_coverage_no_finding()** (3 connections) — `tests/test_findings.py`
- **.test_low_edr_coverage_triggers_high()** (3 connections) — `tests/test_findings.py`
- **.test_no_email_security_triggers_finding()** (3 connections) — `tests/test_findings.py`
- **.test_findings_sorted_by_severity()** (3 connections) — `tests/test_findings.py`
- **.test_admin_mfa_enabled_no_finding()** (3 connections) — `tests/test_findings.py`
- **.test_no_admin_mfa_triggers_critical()** (3 connections) — `tests/test_findings.py`
- **.test_no_org_mfa_triggers_high()** (3 connections) — `tests/test_findings.py`
- **.test_no_priv_account_inventory_triggers_finding()** (3 connections) — `tests/test_findings.py`
- **.test_no_playbooks_triggers_finding()** (3 connections) — `tests/test_findings.py`
- **.test_no_tabletop_triggers_finding()** (3 connections) — `tests/test_findings.py`
- **.test_tested_playbooks_no_finding()** (3 connections) — `tests/test_findings.py`
- **.test_untested_playbooks_triggers_finding()** (3 connections) — `tests/test_findings.py`
- **.test_acceptable_rto_no_finding()** (3 connections) — `tests/test_findings.py`
- *... and 42 more nodes in this community*

## Relationships

- [test_findings.py](test_findings.py.md) (13 shared connections)
- [findings.py](findings.py.md) (4 shared connections)
- [FindingsEngine](FindingsEngine.md) (3 shared connections)
- [calculate_scores](calculate_scores.md) (2 shared connections)
- [generate_narratives](generate_narratives.md) (1 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [api/verification.py](api-verification.py.md) (1 shared connections)
- [test_frameworks.py](test_frameworks.py.md) (1 shared connections)
- [TestRuleCount](TestRuleCount.md) (1 shared connections)

## Source Files

- `app/services/findings.py`
- `tests/test_findings.py`

## Audit Trail

- EXTRACTED: 108 (92%)
- INFERRED: 9 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*