# _make_org

> 52 nodes · cohesion 0.08

## Key Concepts

- **_make_org()** (60 connections) — `tests/test_governance.py`
- **get_applicable_frameworks()** (44 connections) — `app/services/governance/compliance_engine.py`
- **TestComplianceEngineRules** (23 connections) — `tests/test_governance.py`
- **TestComplianceEngineCombinations** (9 connections) — `tests/test_governance.py`
- **.test_dod_with_ai_gov_contractor()** (4 connections) — `tests/test_governance.py`
- **.test_empty_profile()** (4 connections) — `tests/test_governance.py`
- **.test_full_profile_all_flags()** (4 connections) — `tests/test_governance.py`
- **.test_geo_regions_invalid_json()** (4 connections) — `tests/test_governance.py`
- **.test_geo_regions_none()** (4 connections) — `tests/test_governance.py`
- **.test_healthcare_fintech()** (4 connections) — `tests/test_governance.py`
- **.test_reference_urls_populated()** (4 connections) — `tests/test_governance.py`
- **.test_baseline_no_flags_non_tech()** (4 connections) — `tests/test_governance.py`
- **.test_baseline_no_flags_tech_gives_soc2()** (4 connections) — `tests/test_governance.py`
- **.test_pii_eu_no_privacy_framework()** (4 connections) — `tests/test_governance.py`
- **.test_pii_no_eu_gives_privacy_framework()** (4 connections) — `tests/test_governance.py`
- **.test_compliance_engine_import()** (3 connections) — `tests/test_governance.py`
- **.test_ai_production_triggers_ai_rmf()** (3 connections) — `tests/test_governance.py`
- **.test_cardholder_triggers_pci()** (3 connections) — `tests/test_governance.py`
- **.test_dod_triggers_cmmc_and_800_171()** (3 connections) — `tests/test_governance.py`
- **.test_financial_triggers_csf_and_ffiec()** (3 connections) — `tests/test_governance.py`
- **.test_gov_contractor_triggers_fedramp()** (3 connections) — `tests/test_governance.py`
- **.test_no_ai_no_rmf()** (3 connections) — `tests/test_governance.py`
- **.test_no_cardholder_no_pci()** (3 connections) — `tests/test_governance.py`
- **.test_no_dod_no_cmmc()** (3 connections) — `tests/test_governance.py`
- **.test_no_financial_no_csf()** (3 connections) — `tests/test_governance.py`
- *... and 27 more nodes in this community*

## Relationships

- [_make_audit_entry](_make_audit_entry.md) (8 shared connections)
- [Organization](Organization.md) (7 shared connections)
- [TestUptimeTierEnhancements](TestUptimeTierEnhancements.md) (5 shared connections)
- [_make_org](_make_org.md) (4 shared connections)
- [AuditCalendarService](AuditCalendarService.md) (4 shared connections)
- [TechStackService](TechStackService.md) (4 shared connections)
- [TestGovernanceAPI](TestGovernanceAPI.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [._setup](_setup.md) (2 shared connections)
- [TestAuditForecast](TestAuditForecast.md) (2 shared connections)
- [auditor_view](auditor_view.md) (1 shared connections)
- [_get_org](_get_org.md) (1 shared connections)

## Source Files

- `app/services/governance/compliance_engine.py`
- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 146 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*