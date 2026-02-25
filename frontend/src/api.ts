/**
 * AIRS API Client - SINGLE API INTERFACE
 * 
 * All API calls go through this module.
 * Features:
 *   - Uses API_BASE_URL from config (single source of truth)
 *   - Injects Firebase ID token into Authorization header
 *   - Handles 401 errors with redirect to /login
 *   - Provides detailed error messages with status codes and request IDs
 */

import { API_BASE_URL, isDevelopment } from './config';

// =============================================================================
// ERROR TYPES
// =============================================================================

export interface ApiError {
  message: string;
  status?: number;
  requestId?: string;
  detail?: string;
}

export class ApiRequestError extends Error {
  status?: number;
  requestId?: string;
  detail?: string;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiRequestError';
    this.status = error.status;
    this.requestId = error.requestId;
    this.detail = error.detail;
  }

  /**
   * Get a user-friendly error message with all available context
   */
  toDisplayMessage(): string {
    const parts: string[] = [];
    
    if (this.status) {
      parts.push(`[${this.status}]`);
    }
    
    parts.push(this.message);
    
    if (this.requestId) {
      parts.push(`(Request ID: ${this.requestId})`);
    }
    
    return parts.join(' ');
  }
}

// =============================================================================
// TOKEN PROVIDER
// =============================================================================

// Token provider function - set by AuthContext
let tokenProvider: (() => Promise<string | null>) | null = null;

/**
 * Set the token provider function.
 * Called by AuthContext to provide getToken function.
 */
export function setTokenProvider(provider: () => Promise<string | null>) {
  tokenProvider = provider;
}

/**
 * Get authorization headers if token is available.
 */
async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!tokenProvider) return {};
  
  const token = await tokenProvider();
  if (!token) return {};
  
  return { Authorization: `Bearer ${token}` };
}

// =============================================================================
// 401 REDIRECT HANDLING
// =============================================================================

let redirectHandler: (() => void) | null = null;

/**
 * Set the handler for 401 redirects.
 * Called by App component to provide navigation to /login.
 */
export function setUnauthorizedHandler(handler: () => void) {
  redirectHandler = handler;
}

function handleUnauthorized() {
  if (redirectHandler) {
    console.log('[API] 401 Unauthorized - redirecting to login');
    redirectHandler();
  } else {
    console.warn('[API] 401 Unauthorized - no redirect handler set');
  }
}

// =============================================================================
// CORE REQUEST FUNCTION
// =============================================================================

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const method = options.method || 'GET';

  // Get auth headers — errors here are non-fatal (proceed without auth)
  let authHeaders: Record<string, string> = {};
  try {
    authHeaders = await getAuthHeaders();
  } catch (authError) {
    console.warn(`[API] Failed to get auth headers:`, authError);
  }
  
  // Log request
  if (isDevelopment) {
    console.log(`[API] ${method} ${url}`);
  }
  
  // Retry logic for transient network errors (e.g., Cloud Run cold starts)
  const MAX_RETRIES = 2;
  let lastError: unknown;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...options.headers,
        },
      });
    } catch (networkError) {
      lastError = networkError;
      if (attempt < MAX_RETRIES) {
        // Wait before retry: 1s, then 2s
        const delay = (attempt + 1) * 1000;
        console.warn(`[API] Network error for ${method} ${url} (attempt ${attempt + 1}/${MAX_RETRIES + 1}), retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      // All retries exhausted
      console.error(`[API] Network error for ${method} ${url} after ${MAX_RETRIES + 1} attempts:`, networkError);
      throw new ApiRequestError({
        message: `Unable to reach API server. Check your connection and CORS configuration.`,
        detail: `Network request to ${API_BASE_URL} failed after ${MAX_RETRIES + 1} attempts.`,
      });
    }

    // Log response status
    if (isDevelopment) {
      console.log(`[API] ${method} ${url} -> ${response.status}`);
    }

    // Handle 401 - redirect to login
    if (response.status === 401) {
      handleUnauthorized();
      throw new ApiRequestError({
        message: 'Authentication required. Please sign in.',
        status: 401,
      });
    }

    if (!response.ok) {
      let errorMessage = `Request failed`;
      let requestId: string | undefined;
      let detail: string | undefined;
      
      try {
        const errorBody = await response.json();
        if (isDevelopment) {
          console.error(`[API] Error response for ${method} ${url}:`, errorBody);
        }
        
        // Handle structured error response from backend
        if (typeof errorBody === 'object' && errorBody !== null) {
          const err = errorBody as Record<string, unknown>;
          
          // Check for nested error structure
          if (err.error && typeof err.error === 'object') {
            const nested = err.error as Record<string, unknown>;
            errorMessage = String(nested.message || nested.detail || errorMessage);
            if (nested.request_id) {
              requestId = String(nested.request_id);
            }
          } else {
            // Direct error properties
            if (err.detail) {
              errorMessage = String(err.detail);
            } else if (err.message) {
              errorMessage = String(err.message);
            }
            if (err.request_id) {
              requestId = String(err.request_id);
            }
          }
        }
      } catch {
        // Response wasn't JSON
        const text = await response.text().catch(() => '');
        if (isDevelopment) {
          console.error(`[API] Non-JSON error response for ${method} ${url}:`, text);
        }
        if (text) {
          detail = text.slice(0, 200);
        }
      }
      
      // Add status-specific context
      if (response.status === 403) {
        errorMessage = `Access denied: ${errorMessage}`;
      } else if (response.status === 404) {
        errorMessage = `Not found: ${errorMessage}`;
      } else if (response.status >= 500) {
        errorMessage = `Server error: ${errorMessage}`;
      }
      
      throw new ApiRequestError({
        message: errorMessage,
        status: response.status,
        requestId,
        detail,
      });
    }

    return response.json();
  }

  // Unreachable — loop always returns or throws
  throw new ApiRequestError({
    message: `Unable to reach API server. Check your connection and CORS configuration.`,
    detail: `Network request to ${API_BASE_URL} failed.`,
  });
}

// Organizations
export const createOrganization = (data: { name: string; industry?: string; size?: string }) =>
  request<{ id: string; name: string }>('/api/orgs', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getOrganizations = () =>
  request<import('./types').Organization[]>('/api/orgs');

export const getOrganization = (id: string) =>
  request<import('./types').Organization>(`/api/orgs/${id}`);

// Assessments
export const createAssessment = (data: { organization_id: string; title: string }) =>
  request<{ id: string }>('/api/assessments', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getAssessments = () =>
  request<import('./types').Assessment[]>('/api/assessments');

export const getAssessment = (id: string) =>
  request<import('./types').AssessmentDetail>(`/api/assessments/${id}`);

export const submitAnswers = (assessmentId: string, answers: Record<string, string | number | boolean>) => {
  // Transform object format to array format expected by backend
  // Backend expects: { answers: [{ question_id: "tl_01", value: "yes" }, ...] }
  const answersList = Object.entries(answers).map(([questionId, value]) => ({
    question_id: questionId,
    value: String(value), // Backend expects string values
  }));

  return request<{ count: number }>(`/api/assessments/${assessmentId}/answers`, {
    method: 'POST',
    body: JSON.stringify({ answers: answersList }),
  });
};

export const computeScore = (assessmentId: string) =>
  request<import('./types').ScoreResult>(`/api/assessments/${assessmentId}/score`, {
    method: 'POST',
  });

export const getFindings = (assessmentId: string) =>
  request<import('./types').Finding[]>(`/api/assessments/${assessmentId}/findings`);

// Rubric
export const getRubric = () =>
  request<import('./types').Rubric>('/api/scoring/rubric');

// Summary endpoint for executive dashboard
export const getAssessmentSummary = (assessmentId: string) =>
  request<import('./types').AssessmentSummary>(`/api/assessments/${assessmentId}/summary`);

// Report download
export const downloadReport = async (assessmentId: string): Promise<Blob> => {
  const authHeaders = await getAuthHeaders();
  const url = `${API_BASE_URL}/api/assessments/${assessmentId}/report`;
  
  if (isDevelopment) {
    console.log(`[API] GET ${url} (blob)`);
  }
  
  let response: Response;
  try {
    response = await fetch(url, {
      headers: authHeaders,
    });
  } catch (networkError) {
    throw new ApiRequestError({
      message: 'Unable to download report. Check your connection.',
    });
  }
  
  if (response.status === 401) {
    handleUnauthorized();
    throw new ApiRequestError({
      message: 'Authentication required to download report.',
      status: 401,
    });
  }
  
  if (!response.ok) {
    throw new ApiRequestError({
      message: 'Failed to download report',
      status: response.status,
    });
  }
  return response.blob();
};

export const downloadExecutiveSummary = async (assessmentId: string): Promise<Blob> => {
  const authHeaders = await getAuthHeaders();
  const url = `${API_BASE_URL}/api/assessments/${assessmentId}/executive-summary`;

  if (isDevelopment) {
    console.log(`[API] GET ${url} (blob)`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      headers: authHeaders,
    });
  } catch (networkError) {
    throw new ApiRequestError({
      message: 'Unable to download executive summary. Check your connection.',
    });
  }

  if (response.status === 401) {
    handleUnauthorized();
    throw new ApiRequestError({
      message: 'Authentication required to download executive summary.',
      status: 401,
    });
  }

  if (!response.ok) {
    throw new ApiRequestError({
      message: 'Failed to download executive summary',
      status: response.status,
    });
  }
  return response.blob();
};

export const exportAssessmentForSiem = (assessmentId: string) =>
  request<import('./types').SiemExportPayload>(`/api/assessments/${assessmentId}/export`);

// =============================================================================
// REPORTS API (Persistent Reports)
// =============================================================================

export interface ReportFilters {
  organization_id?: string;
  assessment_id?: string;
  report_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// List saved reports
export const getReports = (filters?: ReportFilters) => {
  const params = new URLSearchParams();
  if (filters?.organization_id) params.set('organization_id', filters.organization_id);
  if (filters?.assessment_id) params.set('assessment_id', filters.assessment_id);
  if (filters?.report_type) params.set('report_type', filters.report_type);
  if (filters?.start_date) params.set('start_date', filters.start_date);
  if (filters?.end_date) params.set('end_date', filters.end_date);
  if (filters?.limit) params.set('limit', String(filters.limit));
  if (filters?.offset) params.set('offset', String(filters.offset));
  
  const query = params.toString();
  return request<import('./types').ReportListResponse>(`/api/reports${query ? `?${query}` : ''}`);
};

// Get report details with snapshot
export const getReport = (reportId: string) =>
  request<import('./types').ReportDetail>(`/api/reports/${reportId}`);

// Create a new report for an assessment
export const createReport = (assessmentId: string, data?: { report_type?: string; title?: string }) =>
  request<import('./types').Report>(`/api/assessments/${assessmentId}/reports`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  });

// Download report PDF by report ID
export const downloadReportById = async (reportId: string): Promise<Blob> => {
  const authHeaders = await getAuthHeaders();
  const url = `${API_BASE_URL}/api/reports/${reportId}/download`;
  
  if (isDevelopment) {
    console.log(`[API] GET ${url} (blob)`);
  }
  
  let response: Response;
  try {
    response = await fetch(url, {
      headers: authHeaders,
    });
  } catch (networkError) {
    throw new ApiRequestError({
      message: 'Unable to download report. Check your connection.',
    });
  }
  
  if (response.status === 401) {
    handleUnauthorized();
    throw new ApiRequestError({
      message: 'Authentication required to download report.',
      status: 401,
    });
  }
  
  if (!response.ok) {
    throw new ApiRequestError({
      message: 'Failed to download report',
      status: response.status,
    });
  }
  return response.blob();
};

// Delete a report
export const deleteReport = (reportId: string) =>
  request<void>(`/api/reports/${reportId}`, {
    method: 'DELETE',
  });

// Health check (no auth required)
export const checkHealth = async (): Promise<{ status: string; product?: import('./types').ProductInfo }> => {
  const url = `${API_BASE_URL}/health`;
  if (isDevelopment) {
    console.log(`[API] GET ${url}`);
  }
  
  let response: Response;
  try {
    response = await fetch(url);
  } catch (networkError) {
    throw new ApiRequestError({
      message: `Unable to reach API at ${API_BASE_URL}`,
    });
  }
  
  if (!response.ok) {
    throw new ApiRequestError({
      message: `Health check failed`,
      status: response.status,
    });
  }
  return response.json();
};

export const getSystemStatus = async (): Promise<import('./types').SystemStatus> => {
  const url = `${API_BASE_URL}/health/system`;
  if (isDevelopment) {
    console.log(`[API] GET ${url}`);
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new ApiRequestError({
      message: 'System status check failed',
      status: response.status,
    });
  }
  return response.json();
};

// CORS check (no auth required) - useful for debugging
export const checkCors = async (): Promise<{
  env: string;
  localhost_allowed: boolean;
  allowed_origins: string[];
  request_origin: string | null;
  origin_allowed: boolean;
}> => {
  const url = `${API_BASE_URL}/health/cors`;
  if (isDevelopment) {
    console.log(`[API] GET ${url}`);
  }
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new ApiRequestError({
      message: 'CORS check failed',
      status: response.status,
    });
  }
  return response.json();
};

// Get current API base URL (for debugging)
export const getApiBaseUrl = (): string => API_BASE_URL;

// =============================================================================
// ORGANIZATION ENRICHMENT
// =============================================================================

export const enrichOrganization = (orgId: string, url: string) =>
  request<import('./types').EnrichmentResult>(`/api/orgs/${orgId}/enrich`, {
    method: 'POST',
    body: JSON.stringify({ url }),
  });

// =============================================================================
// ROADMAP TRACKER
// =============================================================================

export const getRoadmap = (assessmentId: string) =>
  request<import('./types').RoadmapResponse>(`/api/assessments/${assessmentId}/roadmap`);

export const createRoadmapItem = (assessmentId: string, data: Partial<import('./types').TrackerItem>) =>
  request<import('./types').TrackerItem>(`/api/assessments/${assessmentId}/roadmap`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateRoadmapItem = (assessmentId: string, itemId: string, data: Partial<import('./types').TrackerItem>) =>
  request<import('./types').TrackerItem>(`/api/assessments/${assessmentId}/roadmap/${itemId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteRoadmapItem = (assessmentId: string, itemId: string) =>
  request<void>(`/api/assessments/${assessmentId}/roadmap/${itemId}`, {
    method: 'DELETE',
  });

// =============================================================================
// INTEGRATIONS (API Keys + Webhooks)
// =============================================================================

export const createApiKey = (orgId: string, scopes: string[] = ['scores:read']) =>
  request<import('./types').ApiKeyCreateResponse>(`/api/orgs/${orgId}/api-keys`, {
    method: 'POST',
    body: JSON.stringify({ scopes }),
  });

export const listApiKeys = (orgId: string) =>
  request<import('./types').ApiKeyMetadata[]>(`/api/orgs/${orgId}/api-keys`);

export const revokeApiKey = (keyId: string) =>
  request<void>(`/api/api-keys/${keyId}`, {
    method: 'DELETE',
  });

export const createWebhook = (
  orgId: string,
  data: { url: string; event_types?: string[]; secret?: string }
) =>
  request<import('./types').Webhook>(`/api/orgs/${orgId}/webhooks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const listWebhooks = (orgId: string) =>
  request<import('./types').Webhook[]>(`/api/orgs/${orgId}/webhooks`);

export const deleteWebhook = (webhookId: string) =>
  request<void>(`/api/webhooks/${webhookId}`, {
    method: 'DELETE',
  });

export const testWebhook = (webhookId: string) =>
  request<{ webhook_id: string; delivered: boolean; status_code?: number; error?: string }>(
    `/api/webhooks/${webhookId}/test`,
    {
      method: 'POST',
    }
  );

export const seedMockSplunkFindings = (orgId?: string) =>
  request<{ org_id: string; source: string; inserted: number; connected: boolean }>(
    '/api/integrations/mock/splunk-seed',
    {
      method: 'POST',
      body: JSON.stringify(orgId ? { org_id: orgId } : {}),
    }
  );

export const getExternalFindings = (params?: { source?: string; limit?: number; orgId?: string }) => {
  const search = new URLSearchParams();
  if (params?.source) search.set('source', params.source);
  if (params?.limit) search.set('limit', String(params.limit));
  if (params?.orgId) search.set('org_id', params.orgId);
  const query = search.toString();
  return request<import('./types').ExternalFinding[]>(
    `/api/integrations/external-findings${query ? `?${query}` : ''}`
  );
};

export const testWebhookUrl = (url: string, secret?: string, eventType = 'assessment.scored.test') =>
  request<import('./types').WebhookUrlTestResponse>(
    '/api/integrations/webhooks/test',
    {
      method: 'POST',
      body: JSON.stringify({
        url,
        secret: secret || undefined,
        event_type: eventType,
      }),
    }
  );

export const getOrgAuditEvents = (orgId: string, limit = 100) =>
  request<import('./types').AuditEvent[]>(`/api/orgs/${orgId}/audit?limit=${limit}`);

export const submitPilotRequest = (data: import('./types').PilotRequestInput) =>
  request<{
    id: string;
    company_name: string;
    team_size: string;
    current_security_tools?: string;
    email: string;
    created_at: string;
  }>('/api/pilot-request', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// =============================================================================
// ENTERPRISE PILOT LEADS (v1)
// =============================================================================

export const submitEnterprisePilotLead = (data: import('./types').EnterprisePilotLeadInput) =>
  request<import('./types').PilotRequestInput & { id: string; created_at: string }>(
    '/api/v1/pilot-leads',
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );

// =============================================================================
// GOVERNANCE & ANALYTICS CONTROL (Phase 5)
// =============================================================================

export const toggleOrgAnalytics = (orgId: string, analyticsEnabled: boolean) =>
  request<import('./types').Organization>(`/api/orgs/${orgId}/analytics`, {
    method: 'PATCH',
    body: JSON.stringify({ analytics_enabled: analyticsEnabled }),
  });

// =============================================================================
// SCORING METHODOLOGY (Phase 4)
// =============================================================================

export const getMethodology = () =>
  request<import('./types').MethodologyResponse>('/api/v1/methodology');

// =============================================================================
// AUDIT EXPORT (Phase 7)
// =============================================================================

export const downloadAuditExport = async (orgId: string): Promise<Blob> => {
  const authHeaders = await getAuthHeaders();
  const url = `${API_BASE_URL}/api/orgs/${orgId}/audit/export`;
  if (isDevelopment) {
    console.log(`[API] GET ${url} (blob)`);
  }
  const response = await fetch(url, { headers: authHeaders });
  if (response.status === 401) {
    handleUnauthorized();
    throw new ApiRequestError({ message: 'Authentication required', status: 401 });
  }
  if (!response.ok) {
    throw new ApiRequestError({ message: 'Failed to download audit log', status: response.status });
  }
  return response.blob();
};

// =============================================================================
// QUESTION SUGGESTIONS
// =============================================================================

export const getSuggestedQuestions = (orgId: string, maxResults = 10) =>
  request<import('./types').SuggestionsResponse>(
    `/api/orgs/${orgId}/suggested-questions?max_results=${maxResults}`
  );

// =============================================================================
// GOVERNANCE — Organization Profile
// =============================================================================

export const getOrganizationProfile = (orgId: string) =>
  request<import('./types').OrganizationProfile>(
    `/api/governance/${orgId}/profile`
  );

export const updateOrganizationProfile = (orgId: string, data: import('./types').OrganizationProfileUpdate) =>
  request<import('./types').OrganizationProfile>(
    `/api/governance/${orgId}/profile`,
    { method: 'PUT', body: JSON.stringify(data) }
  );

// =============================================================================
// GOVERNANCE — Compliance Applicability
// =============================================================================

export const getApplicableFrameworks = (orgId: string) =>
  request<import('./types').ComplianceApplicabilityResponse>(
    `/api/governance/${orgId}/applicable-frameworks`
  );

// =============================================================================
// GOVERNANCE — Uptime Tier Analysis
// =============================================================================

export const getUptimeAnalysis = (orgId: string) =>
  request<import('./types').UptimeTierAnalysis>(
    `/api/governance/${orgId}/uptime-analysis`
  );

// =============================================================================
// GOVERNANCE — Audit Calendar
// =============================================================================

export const getAuditCalendar = (orgId: string) =>
  request<import('./types').AuditCalendarListResponse>(
    `/api/governance/${orgId}/audit-calendar`
  );

export const createAuditCalendarEntry = (orgId: string, data: import('./types').AuditCalendarCreate) =>
  request<import('./types').AuditCalendarEntry>(
    `/api/governance/${orgId}/audit-calendar`,
    { method: 'POST', body: JSON.stringify(data) }
  );

export const updateAuditCalendarEntry = (orgId: string, entryId: string, data: Partial<import('./types').AuditCalendarCreate>) =>
  request<import('./types').AuditCalendarEntry>(
    `/api/governance/${orgId}/audit-calendar/${entryId}`,
    { method: 'PUT', body: JSON.stringify(data) }
  );

export const deleteAuditCalendarEntry = (orgId: string, entryId: string) =>
  request<void>(
    `/api/governance/${orgId}/audit-calendar/${entryId}`,
    { method: 'DELETE' }
  );

export const getAuditForecast = (orgId: string, entryId: string) =>
  request<import('./types').AuditForecast>(
    `/api/governance/${orgId}/audit-calendar/${entryId}/forecast`
  );

// =============================================================================
// GOVERNANCE — Tech Stack Lifecycle
// =============================================================================

export const getTechStack = (orgId: string) =>
  request<import('./types').TechStackListResponse>(
    `/api/governance/${orgId}/tech-stack`
  );

export const createTechStackItem = (orgId: string, data: import('./types').TechStackItemCreate) =>
  request<import('./types').TechStackItem>(
    `/api/governance/${orgId}/tech-stack`,
    { method: 'POST', body: JSON.stringify(data) }
  );

export const updateTechStackItem = (orgId: string, itemId: string, data: Partial<import('./types').TechStackItemCreate>) =>
  request<import('./types').TechStackItem>(
    `/api/governance/${orgId}/tech-stack/${itemId}`,
    { method: 'PUT', body: JSON.stringify(data) }
  );

export const deleteTechStackItem = (orgId: string, itemId: string) =>
  request<void>(
    `/api/governance/${orgId}/tech-stack/${itemId}`,
    { method: 'DELETE' }
  );
