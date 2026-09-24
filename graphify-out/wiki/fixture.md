# fixture

> 14 nodes · cohesion 0.14

## Key Concepts

- **fixture** (7 connections)
- **TestAuditTrailLogging** (6 connections) — `tests/test_reliability.py`
- **db()** (4 connections) — `tests/test_reliability.py`
- **.test_logs_audit_event()** (4 connections) — `tests/test_reliability.py`
- **.test_logs_multiple_events()** (4 connections) — `tests/test_reliability.py`
- **Session** (3 connections)
- **._setup()** (2 connections) — `tests/test_reliability.py`
- **._setup()** (2 connections) — `tests/test_reliability.py`
- **._setup()** (2 connections) — `tests/test_reliability.py`
- **.setup_client()** (2 connections) — `tests/test_reliability.py`
- **Verify RRI audit event logging.** (1 connections) — `tests/test_reliability.py`
- **_log_rri_audit_event creates an AuditEvent record.** (1 connections) — `tests/test_reliability.py`
- **Multiple calls create multiple audit events.** (1 connections) — `tests/test_reliability.py`
- **Yield a clean DB session per test.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [_make_org](_make_org.md) (6 shared connections)
- [test_reliability.py](test_reliability.py.md) (3 shared connections)
- [TestRRIv2API](TestRRIv2API.md) (1 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [_detect_advisories](_detect_advisories.md) (1 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)
- [TestReliabilityAPI](TestReliabilityAPI.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 26 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*