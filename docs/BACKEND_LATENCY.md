# Backend Latency Optimizations

This document describes the caching and performance optimizations implemented for the ResilAI API.

## Summary Caching

### Cached Fields in `assessments` Table

| Field | Type | Description |
|-------|------|-------------|
| `summary_json` | TEXT | Cached JSON payload of the complete summary response |
| `summary_version` | INTEGER | Increments when answers/scoring change (triggers recompute) |
| `summary_computed_at` | DATETIME | Timestamp of when summary was last computed |
| `narrative_executive` | TEXT | Cached LLM-generated executive summary |
| `narrative_roadmap` | TEXT | Cached LLM-generated roadmap narrative |
| `narrative_version` | INTEGER | Version when narratives were generated |
| `narrative_generated_at` | DATETIME | Timestamp of when narratives were generated |

### What Triggers Recompute

| Event | Summary Cache | Narrative Cache |
|-------|---------------|-----------------|
| `submit_answers()` | âœ… Invalidated | âŒ Preserved until summary recomputes |
| `compute_score()` | âœ… Invalidated | âŒ Preserved until summary recomputes |
| First `GET /summary` after invalidation | âœ… Recomputed | âœ… Regenerated if version mismatch |
| Subsequent `GET /summary` (no changes) | âœ… Cache HIT | âœ… Cache HIT |

### Cache Logic Flow

```
GET /api/assessments/{id}/summary
    â”‚
    â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Check assessment.summary_json       â”‚
â”‚ and assessment.summary_computed_at  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â”‚
    â”œâ”€â”€ Cache HIT â”€â”€â–º Return cached summary (+ fresh LLM metadata)
    â”‚
    â””â”€â”€ Cache MISS
            â”‚
            â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ _compute_summary()            â”‚
    â”‚  - domain scores              â”‚
    â”‚  - findings                   â”‚
    â”‚  - roadmap                    â”‚
    â”‚  - framework mapping          â”‚
    â”‚  - analytics                  â”‚
    â”‚  - executive summary          â”‚
    â”‚  - _get_or_generate_narrativesâ”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â”‚
            â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ _get_or_generate_narratives() â”‚
    â”‚                               â”‚
    â”‚ if narrative_version >=       â”‚
    â”‚    summary_version:           â”‚
    â”‚    â†’ Return cached narratives â”‚
    â”‚ else:                         â”‚
    â”‚    â†’ generate_narrative(LLM)  â”‚
    â”‚    â†’ Cache new narratives     â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â”‚
            â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ Cache computed summary        â”‚
    â”‚ assessment.summary_json = ... â”‚
    â”‚ assessment.summary_computed_atâ”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â”‚
            â–¼
    Return summary response
```

## Timing Logs

Key endpoints are logged with `[TIMING]` prefix for monitoring:

| Endpoint Pattern | Log Name |
|------------------|----------|
| `GET /api/organizations` | `org_list` |
| `GET /api/assessments` | `assessments_list` |
| `GET /api/assessments/{id}/summary` | `summary` |
| `GET /api/assessments/{id}/score` | `score` |
| `POST /api/reports` | `report_create` |
| `GET /api/reports/{id}/download` | `report_download` |

### Slow Request Warnings

Requests exceeding **500ms** are logged with `[SLOW]` prefix:

```
[SLOW] [TIMING] summary: GET /api/assessments/abc123/summary status=200 duration=1250.3ms
```

## Dashboard Query Optimization

### `GET /api/assessments` - Recent Parameter

Added `recent=N` query parameter for efficient dashboard queries:

```
GET /api/assessments?recent=5
```

- Limits results to N most recent assessments (max 20)
- Avoids fetching full list when only showing recent items on dashboard
- Uses existing `ORDER BY created_at DESC` with optimized `LIMIT`

## Migration

Run migration `0006_add_summary_caching.py`:

```bash
alembic upgrade head
```

Or via Cloud SQL Proxy:
```bash
cloud-sql-proxy <instance> &
DATABASE_URL=postgresql://user:pass@localhost/airs alembic upgrade head
```

## Performance Expectations

| Scenario | Before | After |
|----------|--------|-------|
| First summary fetch (cold) | ~800-1500ms | ~800-1500ms |
| Subsequent summary fetch (warm) | ~800-1500ms | **~50-100ms** |
| Summary after answer change | ~800-1500ms | ~800-1500ms (recompute) |
| LLM narrative generation | ~2-5s | ~2-5s (first time), **~0ms** (cached) |
