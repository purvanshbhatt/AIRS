package com.example.api

import kotlinx.serialization.Serializable

@Serializable
data class AssessmentSummary(
    val id: String,
    val overall_score: Int,
    val tier: String,
    val framework_coverage: Map<String, Float>,
    val telemetry_active: Boolean
)

@Serializable
data class Finding(
    val id: String,
    val title: String,
    val description: String,
    val severity: Severity,
    val status: FindingStatus,
    val mapped_controls: List<String>,
    val telemetry_verified: Boolean
)

enum class Severity {
    CRITICAL, HIGH, MEDIUM, LOW, INFO
}

enum class FindingStatus {
    OPEN, MITIGATED, RESOLVED
}
