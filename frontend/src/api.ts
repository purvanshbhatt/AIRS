/**
 * AIRS API Client - SINGLE API INTERFACE
 * 
 * All API calls go through this module.
 * Features:
 *   - Uses API_BASE_URL from config (single source of truth)
 *   - Injects Firebase ID token into Authorization header
 *   - Handles 401 errors with redirect to /login
 *   - Provides detailed error messages with status codes and request IDs
 *   - Distinguishes network errors from HTTP errors
 *   - Supports retry for transient failures (e.g., Cloud Run cold starts)
 */

import { API_BASE_URL, isDevelopment } from './config';

export const getApiBaseUrl = () => API_BASE_URL;

// =============================================================================
// ERROR TYPES
// =============================================================================

export type ApiErrorType = 'network' | 'http' | 'cors' | 'timeout' | 'unknown';

export interface ApiError {
  message: string;
  status?: number;
  requestId?: string;
  detail?: string;
  errorType?: ApiErrorType;
}

export class ApiRequestError extends Error {
  status?: number;
  requestId?: string;
  detail?: string;
  errorType: ApiErrorType;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiRequestError';
    this.status = error.status;
    this.requestId = error.requestId;
    this.detail = error.detail;
    this.errorType = error.errorType || (error.status ? 'http' : 'network');
  }

  /**
   * Check if this is a network-level error (no response from server)
   */
  isNetworkError(): boolean {
    return this.errorType === 'network' || this.errorType === 'cors';
  }

  /**
   * Check if this is an HTTP error (server responded with error status)
   */
  isHttpError(): boolean {
    return this.errorType === 'http' && this.status !== undefined;
  }

  /**
   * Get a user-friendly error message with all available context
   */
  toDisplayMessage(): string {
    const parts: string[] = [];

    if (this.status) {
      parts.push(`[${this.status}]`);
    } else if (this.errorType === 'network') {
      parts.push('[Network Error]');
    } else if (this.errorType === 'cors') {
      parts.push('[CORS Error]');
    }

    parts.push(this.message);

    if (this.requestId) {
      parts.push(`(Request ID: ${this.requestId})`);
    }

    return parts.join(' ');
  }

  /**
   * Get a short diagnostic summary for the error panel
   */
  toDiagnostic(): { type: string; status?: number; message: string; requestId?: string } {
    return {
      type: this.errorType,
      status: this.status,
      message: this.message,
      requestId: this.requestId,
    };
  }
}

// =============================================================================
// API CALL HISTORY (for debug panel)
// =============================================================================

export interface ApiCallRecord {
  id: string;
  method: string;
  endpoint: string;
  status: number | 'error';
  statusText: string;
  duration: number;
  timestamp: Date;
  requestId?: string;
  errorMessage?: string;
}

const API_CALL_HISTORY_MAX = 10;
let apiCallHistory: ApiCallRecord[] = [];
let historyListeners: ((history: ApiCallRecord[]) => void)[] = [];

/**
 * Get the API call history (last 10 calls).
 */
export function getApiCallHistory(): ApiCallRecord[] {
  return [...apiCallHistory];
}

/**
 * Subscribe to API call history updates.
 */
export function subscribeToApiCallHistory(listener: (history: ApiCallRecord[]) => void): () => void {
  historyListeners.push(listener);
  return () => {
    historyListeners = historyListeners.filter((l) => l !== listener);
  };
}

function recordApiCall(record: ApiCallRecord) {
  apiCallHistory = [record, ...apiCallHistory].slice(0, API_CALL_HISTORY_MAX);
  historyListeners.forEach((listener) => listener(apiCallHistory));
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
  const authHeaders = await getAuthHeaders();
  const method = options.method || 'GET';
  const startTime = Date.now();
  const callId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  // Log request
  if (isDevelopment) {
    console.log(`[API] ${method} ${url}`);
  }

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
    // Network error (CORS, DNS, connection refused, etc.)
    const errorMessage = networkError instanceof Error ? networkError.message : 'Unknown error';
    console.error(`[API] Network error for ${method} ${url}:`, networkError);

    // Detect CORS errors (they often have no message or "Failed to fetch")
    const isCorsLikely = errorMessage === 'Failed to fetch' || 
                         errorMessage.includes('CORS') ||
                         errorMessage.includes('NetworkError');

    // Record failed call
    recordApiCall({
      id: callId,
      method,
      endpoint,
      status: 'error',
      statusText: isCorsLikely ? 'CORS/Network Error' : 'Network Error',
      duration: Date.now() - startTime,
      timestamp: new Date(),
      errorMessage: isCorsLikely 
        ? 'Request blocked - possible CORS issue' 
        : 'Unable to reach API server',
    });

    throw new ApiRequestError({
      message: isCorsLikely 
        ? `Request blocked. This may be a CORS configuration issue.`
        : `Unable to reach API server. Check your connection.`,
      detail: `Network request to ${API_BASE_URL} failed: ${errorMessage}`,
      errorType: isCorsLikely ? 'cors' : 'network',
    });
  }

  // Log response status
  if (isDevelopment) {
    console.log(`[API] ${method} ${url} -> ${response.status}`);
  }

  // Handle 401 - redirect to login
  if (response.status === 401) {
    recordApiCall({
      id: callId,
      method,
      endpoint,
      status: 401,
      statusText: 'Unauthorized',
      duration: Date.now() - startTime,
      timestamp: new Date(),
      errorMessage: 'Authentication required',
    });

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

    // Record failed call
    recordApiCall({
      id: callId,
      method,
      endpoint,
      status: response.status,
      statusText: response.statusText || 'Error',
      duration: Date.now() - startTime,
      timestamp: new Date(),
      requestId,
      errorMessage,
    });

    throw new ApiRequestError({
      message: errorMessage,
      status: response.status,
      requestId,
      detail,
      errorType: 'http',
    });
  }

  // Record successful call
  recordApiCall({
    id: callId,
    method,
    endpoint,
    status: response.status,
    statusText: response.statusText || 'OK',
    duration: Date.now() - startTime,
    timestamp: new Date(),
  });

  return response.json();
}

// =============================================================================
// RETRY WRAPPER (for transient failures like Cloud Run cold starts)
// =============================================================================

async function requestWithRetry<T>(
  endpoint: string,
  options: RequestInit = {},
  retries: number = 1,
  delayMs: number = 1500
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await request<T>(endpoint, options);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      
      // Only retry on network errors or 5xx server errors
      const isRetryable = 
        (err instanceof ApiRequestError && (err.isNetworkError() || (err.status && err.status >= 500))) ||
        !(err instanceof ApiRequestError);
      
      if (!isRetryable || attempt >= retries) {
        throw err;
      }
      
      if (isDevelopment) {
        console.log(`[API] Request failed, retrying in ${delayMs}ms (attempt ${attempt + 1}/${retries + 1})`);
      }
      
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  
  throw lastError;
}

// Organizations
export const createOrganization = async (data: { name: string; industry?: string; size?: string; website_url?: string }) => {
  const result = await request<{ id: string; name: string }>('/api/orgs', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  // Invalidate cache after create
  const { invalidateAfterMutation } = await import('./cache');
  invalidateAfterMutation('org');
  return result;
};

export const enrichOrganization = (orgId: string, websiteUrl: string) =>
  request<{
    title?: string;
    description?: string;
    keywords: string[];
    baseline_suggestion?: string;
    confidence: number;
    source_url: string;
  }>(`/api/orgs/${orgId}/enrich`, {
    method: 'POST',
    body: JSON.stringify({ website_url: websiteUrl }),
  });

export const getOrganizations = async () => {
  const { cachedFetch, CACHE_KEYS, CACHE_TTL } = await import('./cache');
  return cachedFetch<import('./types').Organization[]>(
    CACHE_KEYS.ORGANIZATIONS,
    () => request<import('./types').Organization[]>('/api/orgs'),
    CACHE_TTL.LIST
  );
};

export const getOrganization = (id: string) =>
  request<import('./types').Organization>(`/api/orgs/${id}`);

// Assessments
export const createAssessment = async (data: { organization_id: string; title: string }) => {
  const result = await request<{ id: string }>('/api/assessments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  // Invalidate cache after create
  const { invalidateAfterMutation } = await import('./cache');
  invalidateAfterMutation('assessment');
  return result;
};

export const getAssessments = async () => {
  const { cachedFetch, CACHE_KEYS, CACHE_TTL } = await import('./cache');
  return cachedFetch<import('./types').Assessment[]>(
    CACHE_KEYS.ASSESSMENTS,
    () => request<import('./types').Assessment[]>('/api/assessments'),
    CACHE_TTL.LIST
  );
};

export const getAssessment = (id: string) =>
  request<import('./types').AssessmentDetail>(`/api/assessments/${id}`);

export const submitAnswers = async (assessmentId: string, answers: Record<string, string | number | boolean>) => {
  // Transform object format to array format expected by backend
  // Backend expects: { answers: [{ question_id: "tl_01", value: "yes" }, ...] }
  const answersList = Object.entries(answers).map(([questionId, value]) => ({
    question_id: questionId,
    value: String(value), // Backend expects string values
  }));

  const result = await request<{ count: number }>(`/api/assessments/${assessmentId}/answers`, {
    method: 'POST',
    body: JSON.stringify({ answers: answersList }),
  });
  
  // Invalidate cache after submitting answers
  const { invalidateAfterMutation, apiCache, CACHE_KEYS } = await import('./cache');
  invalidateAfterMutation('assessment');
  apiCache.invalidate(CACHE_KEYS.SUMMARY(assessmentId));
  
  return result;
};

export const updateAnswers = (assessmentId: string, answers: Record<string, string | number | boolean>) => {
  // Transform object format to array format expected by backend
  // Backend expects: { answers: [{ question_id: "tl_01", value: "yes" }, ...] }
  const answersList = Object.entries(answers).map(([questionId, value]) => ({
    question_id: questionId,
    value: String(value), // Backend expects string values
  }));

  return request<{ count: number }>(`/api/assessments/${assessmentId}/answers`, {
    method: 'PUT',
    body: JSON.stringify({ answers: answersList }),
  });
};

// Edit Mode specific endpoints
export const getAssessmentEdit = (assessmentId: string) =>
  request<{ assessment: import('./types').AssessmentDetail; answers_map: Record<string, any> }>(
    `/api/assessments/${assessmentId}/edit`
  );

export const updateAssessmentEdit = (assessmentId: string, answers: Record<string, any>) => {
  // Same transformation as submitAnswers
  const answersList = Object.entries(answers).map(([questionId, value]) => ({
    question_id: questionId,
    value: String(value),
  }));

  return request<{ count: number }>(`/api/assessments/${assessmentId}/edit`, {
    method: 'PUT',
    body: JSON.stringify({ answers: answersList }),
  });
};

export const computeScore = async (assessmentId: string) => {
  const result = await request<import('./types').ScoreResult>(`/api/assessments/${assessmentId}/score`, {
    method: 'POST',
  });
  
  // Invalidate cache after scoring
  const { invalidateAfterMutation, apiCache, CACHE_KEYS } = await import('./cache');
  invalidateAfterMutation('assessment');
  apiCache.invalidate(CACHE_KEYS.SUMMARY(assessmentId));
  
  return result;
};

export const getFindings = (assessmentId: string) =>
  request<import('./types').Finding[]>(`/api/assessments/${assessmentId}/findings`);

// Rubric
export const getRubric = () =>
  request<import('./types').Rubric>('/api/scoring/rubric');

// Summary endpoint for executive dashboard (uses retry for Cloud Run cold starts)
export const getAssessmentSummary = async (assessmentId: string) => {
  const { cachedFetch, CACHE_KEYS, CACHE_TTL } = await import('./cache');
  return cachedFetch<import('./types').AssessmentSummary>(
    CACHE_KEYS.SUMMARY(assessmentId),
    () => requestWithRetry<import('./types').AssessmentSummary>(`/api/assessments/${assessmentId}/summary`, {}, 1, 2000),
    CACHE_TTL.SUMMARY
  );
};

// Prefetch summary (non-blocking, for eager loading after scoring)
export const prefetchAssessmentSummary = (assessmentId: string) => {
  // Fire and forget - don't await
  getAssessmentSummary(assessmentId).catch(() => {
    // Silently ignore prefetch errors
    console.log(`[Prefetch] Summary prefetch failed for ${assessmentId}`);
  });
};

// Refresh AI narrative (triggers LLM generation)
export const refreshNarrative = async (assessmentId: string): Promise<{
  assessment_id: string;
  llm_status: 'ready' | 'pending' | 'disabled';
  executive_summary_text: string | null;
  roadmap_narrative_text: string | null;
}> => {
  // Invalidate the summary cache before refreshing
  const { apiCache, CACHE_KEYS } = await import('./cache');
  apiCache.invalidate(CACHE_KEYS.SUMMARY(assessmentId));
  
  return request(`/api/assessments/${assessmentId}/refresh-narrative`, {
    method: 'POST',
  });
};

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
export const getReports = async (filters?: ReportFilters) => {
  const params = new URLSearchParams();
  if (filters?.organization_id) params.set('organization_id', filters.organization_id);
  if (filters?.assessment_id) params.set('assessment_id', filters.assessment_id);
  if (filters?.report_type) params.set('report_type', filters.report_type);
  if (filters?.start_date) params.set('start_date', filters.start_date);
  if (filters?.end_date) params.set('end_date', filters.end_date);
  if (filters?.limit) params.set('limit', String(filters.limit));
  if (filters?.offset) params.set('offset', String(filters.offset));

  const query = params.toString();
  
  // Only cache unfiltered requests
  if (!query) {
    const { cachedFetch, CACHE_KEYS, CACHE_TTL } = await import('./cache');
    return cachedFetch<import('./types').ReportListResponse>(
      CACHE_KEYS.REPORTS,
      () => request<import('./types').ReportListResponse>('/api/reports'),
      CACHE_TTL.LIST
    );
  }
  
  return request<import('./types').ReportListResponse>(`/api/reports?${query}`);
};

// Get report details with snapshot
export const getReport = (reportId: string) =>
  request<import('./types').ReportDetail>(`/api/reports/${reportId}`);

// Create a new report for an assessment
export const createReport = async (assessmentId: string, data?: { report_type?: string; title?: string }) => {
  const result = await request<import('./types').Report>(`/api/assessments/${assessmentId}/reports`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  });
  // Invalidate cache after create
  const { invalidateAfterMutation } = await import('./cache');
  invalidateAfterMutation('report');
  return result;
};

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
export const deleteReport = async (reportId: string) => {
  await request<void>(`/api/reports/${reportId}`, {
    method: 'DELETE',
  });
  // Invalidate cache after delete
  const { invalidateAfterMutation } = await import('./cache');
  invalidateAfterMutation('report');
};

// Get reports for a specific assessment
export const getReportsForAssessment = (assessmentId: string) =>
  request<import('./types').ReportListResponse>(`/api/reports?assessment_id=${assessmentId}`);

// Health check (no auth required)
export const checkHealth = async (): Promise<{ status: string }> => {
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

// =============================================================================
// ROADMAP & TREND API
// =============================================================================

export const getOrganizationTrend = (orgId: string) =>
  request<import('./types').ScoreTrendPoint[]>(`/api/orgs/${orgId}/trend`);

export const getRoadmap = (orgId: string, status?: string) => {
  const query = status ? `?status=${status}` : '';
  return request<import('./types').RoadmapListResponse>(`/api/orgs/${orgId}/roadmap${query}`);
};

export const createRoadmapItem = (orgId: string, data: Omit<import('./types').TrackerItem, 'id' | 'organization_id' | 'created_at' | 'updated_at'>) =>
  request<import('./types').TrackerItem>(`/api/orgs/${orgId}/roadmap`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateRoadmapItem = (itemId: string, data: Partial<import('./types').TrackerItem>) =>
  request<import('./types').TrackerItem>(`/api/roadmap/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const deleteRoadmapItem = (itemId: string) =>
  request<void>(`/api/roadmap/${itemId}`, {
    method: 'DELETE',
  });
