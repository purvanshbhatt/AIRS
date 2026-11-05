# .classify_risk

> 18 nodes · cohesion 0.24

## Key Concepts

- **.classify_risk()** (15 connections) — `app/services/governance/tech_stack.py`
- **TestTechStackRiskClassification** (15 connections) — `tests/test_governance.py`
- **._make_item()** (13 connections) — `tests/test_governance.py`
- **.test_deprecated_overrides_version_gap()** (4 connections) — `tests/test_governance.py`
- **.test_eol_overrides_version_gap()** (4 connections) — `tests/test_governance.py`
- **.test_1_version_behind_is_medium()** (3 connections) — `tests/test_governance.py`
- **.test_2_versions_behind_is_medium()** (3 connections) — `tests/test_governance.py`
- **.test_3_versions_behind_is_high()** (3 connections) — `tests/test_governance.py`
- **.test_5_versions_behind_is_high()** (3 connections) — `tests/test_governance.py`
- **.test_current_is_low()** (3 connections) — `tests/test_governance.py`
- **.test_deprecated_is_high()** (3 connections) — `tests/test_governance.py`
- **.test_eol_is_critical()** (3 connections) — `tests/test_governance.py`
- **.test_lts_current_is_low()** (3 connections) — `tests/test_governance.py`
- **Classify risk level for a single tech stack item.** (1 connections) — `app/services/governance/tech_stack.py`
- **Verify classify_risk deterministic rules.** (1 connections) — `tests/test_governance.py`
- **Create a mock-like TechStackItem for risk testing.** (1 connections) — `tests/test_governance.py`
- **EOL takes precedence even if major_versions_behind=0.** (1 connections) — `tests/test_governance.py`
- **Deprecated takes precedence over version gap of 1.** (1 connections) — `tests/test_governance.py`

## Relationships

- [TechStackService](TechStackService.md) (4 shared connections)
- [test_reliability.py](test_reliability.py.md) (3 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/services/governance/tech_stack.py`
- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 42 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*