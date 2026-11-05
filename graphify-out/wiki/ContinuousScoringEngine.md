# ContinuousScoringEngine

> 43 nodes · cohesion 0.07

## Key Concepts

- **ContinuousScoringEngine** (32 connections) — `app/services/continuous_scoring.py`
- **ScoreSnapshot** (12 connections) — `app/models/score_snapshot.py`
- **.calculate_continuous_score()** (11 connections) — `app/services/continuous_scoring.py`
- **take_score_snapshot()** (6 connections) — `app/api/v1/continuous_scoring.py`
- **detect_score_drift()** (5 connections) — `app/api/v1/continuous_scoring.py`
- **get_continuous_score()** (5 connections) — `app/api/v1/continuous_scoring.py`
- **get_score_timeline()** (5 connections) — `app/api/v1/continuous_scoring.py`
- **Session** (5 connections)
- **.take_snapshot()** (5 connections) — `app/services/continuous_scoring.py`
- **get_framework_coverage()** (4 connections) — `app/api/v1/continuous_scoring.py`
- **get** (4 connections)
- **._calculate_confidence()** (4 connections) — `app/services/continuous_scoring.py`
- **.detect_score_drift()** (4 connections) — `app/services/continuous_scoring.py`
- **._get_latest_assessment_answers()** (4 connections) — `app/services/continuous_scoring.py`
- **._calculate_evidence_freshness()** (3 connections) — `app/services/continuous_scoring.py`
- **._calculate_stale_penalty()** (3 connections) — `app/services/continuous_scoring.py`
- **._calculate_telemetry_bonus()** (3 connections) — `app/services/continuous_scoring.py`
- **.get_score_timeline()** (3 connections) — `app/services/continuous_scoring.py`
- **Any** (3 connections)
- **patch** (3 connections)
- **test_continuous_scoring_stale_penalty()** (3 connections) — `tests/test_continuous_scoring.py`
- **test_score_drift_detection()** (3 connections) — `tests/test_continuous_scoring.py`
- **.__init__()** (2 connections) — `app/services/continuous_scoring.py`
- **post** (1 connections)
- **Get the current live continuous governance score.** (1 connections) — `app/api/v1/continuous_scoring.py`
- *... and 18 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (10 shared connections)
- [Organization](Organization.md) (9 shared connections)
- [Connector](Connector.md) (4 shared connections)
- [mobile.py](mobile.py.md) (3 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (3 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (1 shared connections)
- [calculate_scores](calculate_scores.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/api/v1/continuous_scoring.py`
- `app/models/score_snapshot.py`
- `app/services/continuous_scoring.py`
- `tests/test_continuous_scoring.py`

## Audit Trail

- EXTRACTED: 74 (80%)
- INFERRED: 18 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*