package com.example.api

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Body

import com.resilai.app.data.models.*
import com.resilai.app.data.models.AssessmentSummary
import com.resilai.app.data.models.Finding
import com.google.firebase.FirebaseApp
import com.google.firebase.auth.FirebaseAuth
import com.google.android.gms.tasks.Tasks
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow

object AuthEventManager {
    private val _unauthorizedEvents = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val unauthorizedEvents: SharedFlow<Unit> = _unauthorizedEvents

    fun emitUnauthorized() {
        _unauthorizedEvents.tryEmit(Unit)
    }
}

interface MobileAPIClient {
    // 1. Core Assessment Contracts
    @GET("/api/assessments/{assessment_id}/summary")
    suspend fun getAssessmentSummary(@Path("assessment_id") assessmentId: String): AssessmentSummary

    @POST("/api/assessments/{assessment_id}/score")
    suspend fun computeScore(@Path("assessment_id") assessmentId: String): AssessmentScore

    @GET("/api/assessments/{assessment_id}/findings")
    suspend fun getFindings(@Path("assessment_id") assessmentId: String): List<Finding>

    // 2. Integrations Contracts
    @GET("/api/orgs/{org_id}/api-keys")
    suspend fun listApiKeys(@Path("org_id") orgId: String): List<ApiKeyMetadata>

    @POST("/api/orgs/{org_id}/api-keys")
    suspend fun createApiKey(@Path("org_id") orgId: String): ApiKeyMetadata

    @GET("/api/orgs/{org_id}/webhooks")
    suspend fun listWebhooks(@Path("org_id") orgId: String): List<Webhook>

    @POST("/api/orgs/{org_id}/webhooks")
    suspend fun createWebhook(@Path("org_id") orgId: String): Webhook

    @POST("/api/webhooks/{id}/test")
    suspend fun testWebhook(@Path("id") webhookId: String): WebhookTestResult

    // 3. Report Contracts
    @GET("/api/reports")
    suspend fun getReports(): Map<String, Any> // Typically returns { reports: Report[], total: Int }

    // 4. Health Check
    @GET("/health")
    suspend fun checkHealth(): HealthStatus
}

@JsonClass(generateAdapter = true)
data class HealthStatus(
    @Json(name = "status") val status: String,
    @Json(name = "version") val version: String? = null
)

/**
 * Authentication Interceptor
 * As per AUTH_INTEGRATION.md, Firebase Auth token must be injected as a Bearer token
 * into the Authorization header for protected routes.
 */
class FirebaseAuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val requestBuilder = chain.request().newBuilder()

        try {
            // Check if Firebase is initialized before calling getInstance
            val isInitialized = try {
                FirebaseApp.getInstance()
                true
            } catch (e: Exception) {
                false
            }

            if (isInitialized) {
                val user = FirebaseAuth.getInstance().currentUser
                if (user != null) {
                    val tokenResult = Tasks.await(user.getIdToken(false))
                    val token = tokenResult.token
                    if (!token.isNullOrEmpty()) {
                        requestBuilder.addHeader("Authorization", "Bearer $token")
                    }
                }
            }
        } catch (e: Throwable) {
            // Firebase not initialized or other failure
            android.util.Log.e("FirebaseAuthInterceptor", "Error getting auth token", e)
        }

        val response = chain.proceed(requestBuilder.build())

        if (response.code == 401) {
            AuthEventManager.emitUnauthorized()
        }

        return response
    }
}

object ApiClientFactory {
    fun create(baseUrl: String = "https://airs-api-staging-227825933697.us-central1.run.app"): MobileAPIClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(FirebaseAuthInterceptor())
            .addInterceptor(logging)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create())
            .build()

        return retrofit.create(MobileAPIClient::class.java)
    }
}
