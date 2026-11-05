# calculate_rcs

> 8 nodes · cohesion 0.25

## Key Concepts

- **calculate_rcs()** (18 connections) — `app/services/governance/reliability_engine.py`
- **get_reliability_confidence()** (11 connections) — `app/api/reliability.py`
- **_gather_latest_answers()** (9 connections) — `app/services/governance/reliability_engine.py`
- **ReliabilityConfidenceScore** (4 connections) — `app/services/governance/reliability_engine.py`
- **Fetch the latest assessment answers for an organization.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Reliability Confidence Score (RCS) — measures confidence in resilience posture.…** (1 connections) — `app/services/governance/reliability_engine.py`
- **Calculate the Reliability Confidence Score (RCS). Separate from RRI: RRI =…** (1 connections) — `app/services/governance/reliability_engine.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`

## Relationships

- [TestReliabilityConfidenceScore](TestReliabilityConfidenceScore.md) (10 shared connections)
- [Organization](Organization.md) (6 shared connections)
- [_get_org](_get_org.md) (5 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [_make_org](_make_org.md) (3 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [TestDimensionScorers](TestDimensionScorers.md) (2 shared connections)
- [User](User.md) (1 shared connections)

## Source Files

- `app/api/reliability.py`
- `app/services/governance/reliability_engine.py`

## Audit Trail

- EXTRACTED: 34 (87%)
- INFERRED: 5 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*