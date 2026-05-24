package com.example.data.repository

import com.example.data.local.ResilAIDao
import com.example.data.model.*
import com.example.data.remote.ResilAIService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class ResilAIRepository(
    private val service: ResilAIService,
    private val dao: ResilAIDao
) {
    fun getAssessmentSummary(id: String): Flow<AssessmentSummaryEntity?> = flow {
        // Emit cached data first
        val cached = dao.getAssessmentSummary(id)
        emit(cached)

        try {
            val remote = service.getAssessmentSummary(id)
            val entity = AssessmentSummaryEntity(
                id = remote.id,
                overallScore = remote.overall_score,
                tier = remote.tier,
                telemetryActive = remote.telemetry_active
            )
            dao.insertAssessmentSummary(entity)
            emit(entity)
        } catch (e: Exception) {
            // Serve Last Known Good (already emitted or fallback)
            if (cached == null) throw e
        }
    }

    fun getFindings(id: String): Flow<List<FindingEntity>> = flow {
        val cached = dao.getAllFindings()
        emit(cached)

        try {
            val remoteList = service.getFindings(id)
            val entities = remoteList.map {
                FindingEntity(
                    id = it.id,
                    title = it.title,
                    description = it.description,
                    severity = it.severity,
                    status = it.status,
                    telemetryVerified = it.telemetry_verified
                )
            }
            dao.deleteAllFindings()
            dao.insertFindings(entities)
            emit(entities)
        } catch (e: Exception) {
            if (cached.isEmpty()) throw e
        }
    }
}
