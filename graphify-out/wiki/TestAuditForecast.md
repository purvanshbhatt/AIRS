# TestAuditForecast

> 20 nodes · cohesion 0.14

## Key Concepts

- **TestAuditForecast** (14 connections) — `tests/test_governance.py`
- **._setup_with_findings()** (12 connections) — `tests/test_governance.py`
- **.test_forecast_critical_when_imminent()** (7 connections) — `tests/test_governance.py`
- **Assessment** (3 connections)
- **Finding** (3 connections)
- **.test_forecast_critical_risk()** (3 connections) — `tests/test_governance.py`
- **.test_forecast_high_risk()** (3 connections) — `tests/test_governance.py`
- **.test_forecast_low_risk()** (3 connections) — `tests/test_governance.py`
- **.test_forecast_medium_risk()** (3 connections) — `tests/test_governance.py`
- **.test_forecast_recommendation_text()** (3 connections) — `tests/test_governance.py`
- **.test_framework_keywords_complete()** (2 connections) — `tests/test_governance.py`
- **Test forecast engine logic.** (1 connections) — `tests/test_governance.py`
- **findings_spec: list of (title, severity) tuples. Returns (entry, svc).** (1 connections) — `tests/test_governance.py`
- **3+ critical/high related findings → critical risk.** (1 connections) — `tests/test_governance.py`
- **1-2 critical/high related findings → high risk.** (1 connections) — `tests/test_governance.py`
- **2+ related findings but no critical/high → medium.** (1 connections) — `tests/test_governance.py`
- **No related findings → low risk.** (1 connections) — `tests/test_governance.py`
- **Any critical/high + audit < 30 days → critical.** (1 connections) — `tests/test_governance.py`
- **Verify recommendation strings are set per risk level.** (1 connections) — `tests/test_governance.py`
- **Verify all mapped frameworks have keywords.** (1 connections) — `tests/test_governance.py`

## Relationships

- [Organization](Organization.md) (6 shared connections)
- [AuditCalendarService](AuditCalendarService.md) (4 shared connections)
- [_make_org](_make_org.md) (2 shared connections)
- [_make_audit_entry](_make_audit_entry.md) (1 shared connections)

## Source Files

- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 35 (90%)
- INFERRED: 4 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*