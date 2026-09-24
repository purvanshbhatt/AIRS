# findings.py

> 43 nodes · cohesion 0.10

## Key Concepts

- **findings.py** (37 connections) — `app/services/findings.py`
- **evaluate_ai_governance_findings()** (28 connections) — `app/services/findings.py`
- **Any** (22 connections)
- **TestInventoryClassification** (16 connections) — `tests/test_ai_findings.py`
- **_entry_matches_type()** (9 connections) — `app/services/findings.py`
- **test_ai_findings.py** (6 connections) — `tests/test_ai_findings.py`
- **_rule_ai_agent_framework_attack_surface()** (4 connections) — `app/services/findings.py`
- **_rule_ai_eol_model_dependencies()** (4 connections) — `app/services/findings.py`
- **_rule_ai_mcp_server_internet_facing()** (4 connections) — `app/services/findings.py`
- **_rule_ai_prompt_library_exposure()** (4 connections) — `app/services/findings.py`
- **_rule_ai_unversioned_prompt()** (4 connections) — `app/services/findings.py`
- **_rule_ai_vector_db_no_retention_policy()** (4 connections) — `app/services/findings.py`
- **get_answer()** (3 connections) — `app/services/findings.py`
- **get_edr_pct()** (3 connections) — `app/services/findings.py`
- **get_rto_hours()** (3 connections) — `app/services/findings.py`
- **_rule_ai_air_gapped_disabled()** (3 connections) — `app/services/findings.py`
- **_rule_ai_no_governance_owner()** (3 connections) — `app/services/findings.py`
- **_rule_ai_unclassified_type()** (3 connections) — `app/services/findings.py`
- **_rule_ai_inventory_missing()** (2 connections) — `app/services/findings.py`
- **.test_agent_framework_dev_only_not_match()** (2 connections) — `tests/test_ai_findings.py`
- **.test_agent_framework_production_critical_matches_ai_006()** (2 connections) — `tests/test_ai_findings.py`
- **.test_air_gapped_disabled_pii_matches_ai_009()** (2 connections) — `tests/test_ai_findings.py`
- **.test_determinism()** (2 connections) — `tests/test_ai_findings.py`
- **.test_empty_inventory_emits_only_ai_001()** (2 connections) — `tests/test_ai_findings.py`
- **.test_eol_model_matches_ai_008()** (2 connections) — `tests/test_ai_findings.py`
- *... and 18 more nodes in this community*

## Relationships

- [test_findings.py](test_findings.py.md) (9 shared connections)
- [FindingsEngine](FindingsEngine.md) (6 shared connections)
- [generate_findings](generate_findings.md) (4 shared connections)
- [get_rubric](get_rubric.md) (3 shared connections)
- [test_frameworks.py](test_frameworks.py.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [api/verification.py](api-verification.py.md) (1 shared connections)
- [TestRuleRegistration](TestRuleRegistration.md) (1 shared connections)

## Source Files

- `app/services/findings.py`
- `tests/test_ai_findings.py`

## Audit Trail

- EXTRACTED: 115 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*