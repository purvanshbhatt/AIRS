package com.example.data.repository

import android.util.Log
import com.example.api.MobileAPIClient
import com.example.data.local.ResilAIDao
import com.resilai.app.data.models.AssessmentSummary
import com.resilai.app.data.models.Finding
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import com.example.data.model.AssessmentSummaryEntity
import com.example.data.model.FindingEntity

class ResilAIRepository(
    private val apiClient: MobileAPIClient,
    private val dao: ResilAIDao
) {

    /**
     * Attempts to fetch from network. If it fails, falls back to the "Last Known Good" cache.
     */
    fun getAssessmentSummary(assessmentId: String): Flow<Result<AssessmentSummary>> = flow {
        try {
            // Attempt network fetch
            val networkResult = apiClient.getAssessmentSummary(assessmentId)
            
            // Map to entity and cache
            val entity = AssessmentSummaryEntity(
                id = networkResult.id,
                organizationId = networkResult.organization_id,
                overallScore = networkResult.overall_score,
                tier = networkResult.tier,
                // Simplified mapping for demonstration
                findingsJson = "[]",
                frameworkMappingJson = "[]",
                roadmapJson = "[]",
                analyticsJson = "{}"
            )
            dao.insertAssessmentSummary(entity)
            
            emit(Result.success(networkResult))
        } catch (e: Exception) {
            Log.e("ResilAIRepository", "Network fetch failed, falling back to cache", e)
            
            // Fallback to cache
            val cachedResult = dao.getAssessmentSummary(assessmentId)
            if (cachedResult != null) {
                // Map back to Domain Model
                val fallbackSummary = AssessmentSummary(
                    id = cachedResult.id,
                    organization_id = cachedResult.organizationId,
                    overall_score = cachedResult.overallScore,
                    tier = cachedResult.tier,
                    findings = emptyList(),
                    framework_mapping = emptyList(),
                    roadmap = emptyList(),
                    detailed_roadmap = emptyList(),
                    analytics = emptyMap(),
                    executive_summary = "OFFLINE CACHE"
                )
                emit(Result.success(fallbackSummary))
            } else {
                emit(Result.failure(e))
            }
        }
    }
}
