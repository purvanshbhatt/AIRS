# TestGovernanceAPI

> 12 nodes · cohesion 0.21

## Key Concepts

- **TestGovernanceAPI** (10 connections) — `tests/test_governance.py`
- **._create_org()** (5 connections) — `tests/test_governance.py`
- **.setup_client()** (3 connections) — `tests/test_governance.py`
- **fixture** (2 connections)
- **.test_applicable_frameworks_endpoint()** (2 connections) — `tests/test_governance.py`
- **.test_get_profile_empty()** (2 connections) — `tests/test_governance.py`
- **.test_update_profile()** (2 connections) — `tests/test_governance.py`
- **.test_uptime_analysis_not_configured()** (2 connections) — `tests/test_governance.py`
- **.test_uptime_analysis_on_track()** (2 connections) — `tests/test_governance.py`
- **Integration tests for governance API endpoints.** (1 connections) — `tests/test_governance.py`
- **Set up test client with DB override.** (1 connections) — `tests/test_governance.py`
- **.test_profile_404_unknown_org()** (1 connections) — `tests/test_governance.py`

## Relationships

- [_make_org](_make_org.md) (3 shared connections)
- [_make_audit_entry](_make_audit_entry.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*