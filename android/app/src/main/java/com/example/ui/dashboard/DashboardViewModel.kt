package com.example.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.resilai.app.data.models.ApiKeyMetadata
import com.example.api.ApiClientFactory
import com.resilai.app.data.models.AssessmentScore
import com.resilai.app.data.models.AssessmentSummary
import com.resilai.app.data.models.Finding
import com.example.api.MobileAPIClient
import com.resilai.app.data.models.Webhook
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class DashboardState {
    object Loading : DashboardState()
    data class Success(
        val summary: AssessmentSummary,
        val score: AssessmentScore,
        val findings: List<Finding>,
        val apiKeys: List<ApiKeyMetadata>,
        val webhooks: List<Webhook>,
        val health: String = "OK"
    ) : DashboardState()
    data class Error(val message: String, val isBackendDown: Boolean = false) : DashboardState()
}

class DashboardViewModel(
    private val apiClient: MobileAPIClient = ApiClientFactory.create()
) : ViewModel() {
    private val _state = MutableStateFlow<DashboardState>(DashboardState.Loading)
    val state: StateFlow<DashboardState> = _state.asStateFlow()
    
    // Toggle for Executive / Forensic log view
    private val _isForensicMode = MutableStateFlow(false)
    val isForensicMode: StateFlow<Boolean> = _isForensicMode.asStateFlow()

    init {
        loadData()
    }

    fun toggleMode() {
        _isForensicMode.value = !_isForensicMode.value
    }

    fun loadData() {
        viewModelScope.launch {
            _state.value = DashboardState.Loading
            try {
                // Check Backend Health first as per new contract verification requirements
                val health = try {
                    apiClient.checkHealth()
                } catch (e: Exception) {
                    _state.value = DashboardState.Error("Backend Service Unreachable", isBackendDown = true)
                    return@launch
                }

                // In a real app we fetch this id from navigation arguments or a user session
                val assessmentId = "assessment_demo_1" // Demo ID for staging
                val orgId = "org_demo"
                
                // We use try-catch or async for multiple calls to avoid failure if one fails, but let's do sequential for now
                val summary = apiClient.getAssessmentSummary(assessmentId)
                val score = apiClient.computeScore(assessmentId)
                
                // You can also fetch findings directly via getFindings, though summary has them
                val findings = apiClient.getFindings(assessmentId)
                
                val apiKeys = try { apiClient.listApiKeys(orgId) } catch (e: Exception) { emptyList() }
                val webhooks = try { apiClient.listWebhooks(orgId) } catch (e: Exception) { emptyList() }
                
                _state.value = DashboardState.Success(
                    summary = summary,
                    score = score,
                    findings = findings,
                    apiKeys = apiKeys,
                    webhooks = webhooks,
                    health = health.status
                )
            } catch (e: Exception) {
                _state.value = DashboardState.Error(e.message ?: "Unknown error occurred")
            }
        }
    }
}
