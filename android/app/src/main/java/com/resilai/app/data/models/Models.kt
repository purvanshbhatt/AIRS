package com.resilai.app.data.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class AssessmentSummary(
    val id: String,
    @Json(name = "organization_id") val organizationId: String,
    @Json(name = "overall_score") val overallScore: Double,
    val tier: String,
    val findings: List<Finding>,
    @Json(name = "framework_mapping") val frameworkMapping: FrameworkMapping?,
    val roadmap: Map<String, List<RoadmapItem>>?,
    @Json(name = "detailed_roadmap") val detailedRoadmap: Map<String, Any>?,
    val analytics: Map<String, Any>?,
    @Json(name = "executive_summary") val executiveSummary: Map<String, Any>?,
    @Json(name = "executive_summary_text") val executiveSummaryText: String?,
    @Json(name = "roadmap_narrative_text") val roadmapNarrativeText: String?,
    @Json(name = "llm_enabled") val llmEnabled: Boolean? = null
)

@JsonClass(generateAdapter = true)
data class FrameworkMapping(
    val coverage: Double?,
    val findings: List<MappedFinding>
)

@JsonClass(generateAdapter = true)
data class MappedFinding(
    @Json(name = "finding_id") val findingId: String,
    val title: String,
    val severity: String,
    @Json(name = "mitre_refs") val mitreRefs: List<String>? = emptyList(),
    @Json(name = "cis_refs") val cisRefs: List<String>? = emptyList(),
    @Json(name = "owasp_refs") val owaspRefs: List<String>? = emptyList()
)

@JsonClass(generateAdapter = true)
data class RoadmapItem(
    val title: String,
    val description: String
)

@JsonClass(generateAdapter = true)
data class Finding(
    @Json(name = "finding_id") val findingId: String? = null,
    val id: String? = null,
    val title: String,
    val severity: String
)

@JsonClass(generateAdapter = true)
data class AssessmentScore(
    @Json(name = "assessment_id") val assessmentId: String,
    @Json(name = "overall_score") val overallScore: Double,
    @Json(name = "maturity_level") val maturityLevel: Int,
    @Json(name = "maturity_name") val maturityName: String,
    @Json(name = "domain_scores") val domainScores: Map<String, Double> = emptyMap(),
    @Json(name = "findings_count") val findingsCount: Int,
    @Json(name = "high_severity_count") val highSeverityCount: Int
)

@JsonClass(generateAdapter = true)
data class ApiKeyMetadata(
    val id: String,
    @Json(name = "org_id") val orgId: String,
    val prefix: String,
    val scopes: List<String>,
    @Json(name = "api_key") val apiKey: String? = null,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class Report(
    val id: String,
    val name: String?,
    @Json(name = "created_at") val createdAt: String?
)

@JsonClass(generateAdapter = true)
data class Webhook(
    val id: String,
    @Json(name = "org_id") val orgId: String,
    val url: String,
    @Json(name = "created_at") val createdAt: String? = null
)

@JsonClass(generateAdapter = true)
data class WebhookTestResult(
    @Json(name = "webhook_id") val webhookId: String,
    val delivered: Boolean,
    @Json(name = "status_code") val statusCode: Int?,
    val error: String?
)
