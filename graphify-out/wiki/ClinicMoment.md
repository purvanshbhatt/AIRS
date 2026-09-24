# ClinicMoment

> 23 nodes · cohesion 0.13

## Key Concepts

- **ClinicMoment** (35 connections) — `app/services/clinic_engine/v2/schema.py`
- **MorningCheckGeneratorV2** (12 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **v2/morning_check.py** (9 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **TestMorningCheckV2** (8 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **TestCausalityProof** (7 connections) — `tests/test_production_org_lifecycle.py`
- **MorningCheckV2** (6 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **.test_deterministic_scoring_causality()** (6 connections) — `tests/test_production_org_lifecycle.py`
- **.generate()** (5 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **QuestionSummary** (4 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **.test_concern_only()** (3 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_multiple_critical()** (3 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_needs_attention_critical()** (3 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_all_clear()** (2 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **ClinicMoment** (1 connections)
- **V2 Morning Check Generator — Real telemetry, real moments. Consumes the V2…** (1 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **Summary of how one customer question was answered.** (1 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **The Morning Safety Check a clinic owner sees.** (1 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **Generates the Morning Safety Check from V2 ClinicMoments.** (1 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **Build the morning check from evaluated moments.** (1 connections) — `app/services/clinic_engine/v2/morning_check.py`
- **The complete output: what happened, why, and what to do.** (1 connections) — `app/services/clinic_engine/v2/schema.py`
- **Tests for the Morning Safety Check generator.** (1 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **Test Phase 12: Score changes when evidence changes, and reverts when restored.** (1 connections) — `tests/test_production_org_lifecycle.py`
- **Score must change with evidence and revert when evidence is restored.** (1 connections) — `tests/test_production_org_lifecycle.py`

## Relationships

- [schema.py](schema.py.md) (16 shared connections)
- [contracts.py](contracts.py.md) (10 shared connections)
- [router.py](router.py.md) (8 shared connections)
- [test_explainability.py](test_explainability.py.md) (4 shared connections)
- [BaseModel](BaseModel.md) (3 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (3 shared connections)
- [Evidence](Evidence.md) (1 shared connections)

## Source Files

- `app/services/clinic_engine/v2/morning_check.py`
- `app/services/clinic_engine/v2/schema.py`
- `tests/services/clinic_engine/test_v2_engine.py`
- `tests/test_production_org_lifecycle.py`

## Audit Trail

- EXTRACTED: 62 (78%)
- INFERRED: 17 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*