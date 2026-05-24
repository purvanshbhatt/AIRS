package com.example.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import kotlinx.serialization.Serializable

@Serializable
data class AssessmentSummary(
    val id: String,
    val overall_score: Int,
    val tier: String,
    val framework_coverage: Map<String, Float>,
    val telemetry_active: Boolean
)

@Entity(tableName = "assessment_summary")
data class AssessmentSummaryEntity(
    @PrimaryKey val id: String,
    val overallScore: Int,
    val tier: String,
    val telemetryActive: Boolean,
    val lastUpdated: Long = System.currentTimeMillis()
)

@Serializable
data class Finding(
    val id: String,
    val title: String,
    val description: String,
    val severity: String,
    val status: String,
    val mapped_controls: List<String>,
    val telemetry_verified: Boolean
)

@Entity(tableName = "findings")
data class FindingEntity(
    @PrimaryKey val id: String,
    val title: String,
    val description: String,
    val severity: String,
    val status: String,
    val telemetryVerified: Boolean
)
