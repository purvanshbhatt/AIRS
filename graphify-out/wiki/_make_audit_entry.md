# _make_audit_entry

> 25 nodes · cohesion 0.12

## Key Concepts

- **_make_audit_entry()** (14 connections) — `tests/test_governance.py`
- **_make_finding()** (12 connections) — `tests/test_governance.py`
- **TestAuditReadinessScore** (10 connections) — `tests/test_governance.py`
- **.test_score_floor_at_zero()** (7 connections) — `tests/test_governance.py`
- **.test_score_mixed_severities()** (7 connections) — `tests/test_governance.py`
- **.test_score_with_critical()** (7 connections) — `tests/test_governance.py`
- **.test_score_with_high()** (7 connections) — `tests/test_governance.py`
- **.test_score_with_medium()** (7 connections) — `tests/test_governance.py`
- **Session** (5 connections)
- **.test_score_in_forecast_response_schema()** (5 connections) — `tests/test_governance.py`
- **.test_score_perfect_no_findings()** (5 connections) — `tests/test_governance.py`
- **db()** (4 connections) — `tests/test_governance.py`
- **AuditCalendarEntry** (1 connections)
- **Severity** (1 connections)
- **Create a finding attached to the given assessment.** (1 connections) — `tests/test_governance.py`
- **Test the audit_readiness_score computation in forecast.** (1 connections) — `tests/test_governance.py`
- **No related findings → score = 100.** (1 connections) — `tests/test_governance.py`
- **Critical findings reduce score by 15 each.** (1 connections) — `tests/test_governance.py`
- **High findings reduce score by 8 each.** (1 connections) — `tests/test_governance.py`
- **Medium findings reduce score by 3 each.** (1 connections) — `tests/test_governance.py`
- **Mixed severities: 100 - 15 - 8 - 3 = 74.** (1 connections) — `tests/test_governance.py`
- **Score should never go below 0.** (1 connections) — `tests/test_governance.py`
- **Verify audit_readiness_score is returned in the forecast schema.** (1 connections) — `tests/test_governance.py`
- **Create an audit calendar entry 60 days from now.** (1 connections) — `tests/test_governance.py`
- **Yield a clean DB session per test.** (1 connections) — `tests/test_governance.py`

## Relationships

- [Organization](Organization.md) (14 shared connections)
- [AuditCalendarService](AuditCalendarService.md) (9 shared connections)
- [_make_org](_make_org.md) (8 shared connections)
- [TestGovernanceAPI](TestGovernanceAPI.md) (1 shared connections)
- [TestAuditForecast](TestAuditForecast.md) (1 shared connections)

## Source Files

- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 65 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*