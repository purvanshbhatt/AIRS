# ResilAI Frontend/Backend Contract Map

This map documents the current runtime contracts used by the frontend, with focus on framework mapping, roadmap, analytics, scoring, narratives, and reporting.

## Core Assessment Contracts

| Frontend call | Backend route | Response shape used by UI |
|---|---|---|
| `getAssessmentSummary(assessmentId)` (`frontend/src/api.ts`) | `GET /api/assessments/{assessment_id}/summary` | `{ id, organization_id, overall_score, tier, findings, framework_mapping, roadmap, detailed_roadmap, analytics, executive_summary, executive_summary_text, roadmap_narrative_text, llm_* }` |
| `computeScore(assessmentId)` | `POST /api/assessments/{assessment_id}/score` | `{ assessment_id, overall_score, maturity_level, maturity_name, domain_scores[], findings_count, high_severity_count }` |
| `getFindings(assessmentId)` | `GET /api/assessments/{assessment_id}/findings` | `Finding[]` |

## Framework Mapping (MITRE/CIS/OWASP)

| Frontend usage | Backend source | Required fields |
|---|---|---|
| `summary.framework_mapping` (`FrameworkTab` in `frontend/src/components/ResultsTabs.tsx`) | `GET /api/assessments/{assessment_id}/summary` | `framework_mapping.findings[]` with `finding_id`, `title`, `severity`, `mitre_refs[]`, `cis_refs[]`, `owasp_refs[]`; and `framework_mapping.coverage` |

## Roadmap Contracts

| Frontend call | Backend route | Response shape used by UI |
|---|---|---|
| `summary.roadmap` / `summary.detailed_roadmap` (`RoadmapTab`) | `GET /api/assessments/{assessment_id}/summary` | `roadmap.day30/day60/day90[]`; `detailed_roadmap.phases[].items[]` |
| `getRoadmap(assessmentId)` | `GET /api/assessments/{assessment_id}/roadmap` | `{ items: TrackerItem[], total }` |
| `createRoadmapItem(assessmentId, data)` | `POST /api/assessments/{assessment_id}/roadmap` | `TrackerItem` |
| `updateRoadmapItem(assessmentId, itemId, data)` | `PUT /api/assessments/{assessment_id}/roadmap/{item_id}` | `TrackerItem` |
| `deleteRoadmapItem(assessmentId, itemId)` | `DELETE /api/assessments/{assessment_id}/roadmap/{item_id}` | `204 No Content` |

Backward compatibility: roadmap endpoints also resolve legacy organization ID inputs by selecting latest assessment for that org.

## Analytics Contracts

| Frontend usage | Backend source | Required fields |
|---|---|---|
| `summary.analytics.attack_paths` (`AnalyticsTab`) | `GET /api/assessments/{assessment_id}/summary` | `attack_paths[]` with `id`, `name`, `description`, `risk_level`, `techniques[]`, `enabling_gaps[]`, `likelihood`, `impact` |
| `summary.analytics.detection_gaps/response_gaps/identity_gaps` | same | `{ categories[] }` where each category supports both legacy and new fields: `name`, `category`, `gaps`, `gap_count`, `severity`, `is_critical`, `description`, `findings[]` |
| `summary.analytics.risk_summary` | same | `overall_risk_level`, `key_risks`, `mitigating_factors`, plus compatibility fields: `severity_counts`, `findings_count`, `total_risk_score`, `attack_paths_enabled`, `total_gaps_identified` |

## Report Contracts

| Frontend call | Backend route | Response shape |
|---|---|---|
| `downloadReport(assessmentId)` | `GET /api/assessments/{assessment_id}/report` | PDF blob (legacy direct report) |
| `createReport(assessmentId)` | `POST /api/assessments/{assessment_id}/reports` | persisted report metadata |
| `getReports(...)` | `GET /api/reports` | `{ reports: Report[], total }` |
| `downloadReportById(reportId)` | `GET /api/reports/{report_id}/download` | PDF blob |

## Narrative Contracts

| Frontend/backend usage | Backend route | Response shape |
|---|---|---|
| LLM status check (docs/ops) | `GET /health/llm` | `{ llm_enabled, llm_provider, llm_model, demo_mode, runtime_check }` |
| Narrative API (optional) | `GET /api/narratives/status`, `POST /api/narratives/{assessment_id}/narratives` | LLM availability and generated narrative payload |

## Integration Contracts (New)

| Frontend call | Backend route | Response shape |
|---|---|---|
| `createApiKey(orgId)` | `POST /api/orgs/{org_id}/api-keys` | returns one-time plaintext key: `{ id, org_id, prefix, scopes, api_key, created_at }` |
| `listApiKeys(orgId)` | `GET /api/orgs/{org_id}/api-keys` | `ApiKeyMetadata[]` |
| `createWebhook(orgId, ...)` | `POST /api/orgs/{org_id}/webhooks` | `Webhook` |
| `listWebhooks(orgId)` | `GET /api/orgs/{org_id}/webhooks` | `Webhook[]` |
| `testWebhook(id)` | `POST /api/webhooks/{id}/test` | `{ webhook_id, delivered, status_code, error }` |
| External pull contract | `GET /api/external/latest-score` (`X-AIRS-API-Key`) | `{ org_id, assessment_id, timestamp, overall_score, risk_summary, top_findings[] }` |
