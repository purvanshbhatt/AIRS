# Backend Latency Optimizations

This document summarizes backend caching and performance behavior used by ResilAI summary endpoints.

## Summary Cache Model

Cached fields on assessments include:

- `summary_json`
- `summary_version`
- `summary_computed_at`
- `narrative_executive`
- `narrative_roadmap`
- `narrative_version`
- `narrative_generated_at`

## Recompute Triggers

| Event | Summary Cache | Narrative Cache |
| --- | --- | --- |
| `submit_answers()` | Invalidated | Preserved until summary recompute |
| `compute_score()` | Invalidated | Preserved until summary recompute |
| First summary call after invalidation | Recomputed | Regenerated if version mismatch |
| Subsequent summary call without changes | Cache hit | Cache hit |

## Runtime Flow

```mermaid
flowchart TD
  A[GET /api/assessments/{id}/summary] --> B{Summary cache valid?}
  B -->|Yes| C[Return cached summary]
  B -->|No| D[Recompute summary payload]
  D --> E{Narratives version current?}
  E -->|Yes| F[Reuse cached narratives]
  E -->|No| G[Generate narrative content]
  F --> H[Persist summary cache]
  G --> H
  H --> I[Return summary response]
```

## Timing Telemetry

Common timed endpoints:

- `org_list`
- `assessments_list`
- `summary`
- `score`
- `report_create`
- `report_download`

Slow requests over `500ms` should be logged for diagnostics.

## Dashboard Query Optimization

`GET /api/assessments?recent=N` supports efficient dashboard loading by limiting result size.

## Migrations

Run latest migrations:

```bash
alembic upgrade head
```

Cloud SQL proxy path (optional):

```bash
cloud-sql-proxy <instance> &
DATABASE_URL=postgresql://user:pass@localhost/airs alembic upgrade head
```

## Expected Performance

| Scenario | Typical Range |
| --- | --- |
| First summary fetch (cold) | ~800-1500ms |
| Warm summary fetch (cache hit) | ~50-100ms |
| Summary after answer changes | ~800-1500ms |
| Narrative generation | ~2-5s first call, near-zero when cached |
