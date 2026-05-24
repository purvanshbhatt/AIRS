package com.example.data.remote

import com.example.data.model.AssessmentSummary
import com.example.data.model.Finding
import retrofit2.http.GET
import retrofit2.http.Path

interface ResilAIService {
    @GET("api/assessments/{id}/summary")
    suspend fun getAssessmentSummary(@Path("id") id: String): AssessmentSummary

    @GET("api/assessments/{id}/findings")
    suspend fun getFindings(@Path("id") id: String): List<Finding>
}
