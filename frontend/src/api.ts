// API client for AIRS backend

import { apiBaseUrl } from './config';

const API_BASE = apiBaseUrl;

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

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const authHeaders = await getAuthHeaders();
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Organizations
export const createOrganization = (data: { name: string; industry?: string; size?: string }) =>
  request<{ id: string; name: string }>('/api/orgs', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getOrganizations = () =>
  request<Array<{ id: string; name: string }>>('/api/orgs');

// Assessments
export const createAssessment = (data: { organization_id: string; title: string }) =>
  request<{ id: string }>('/api/assessments', {
    method: 'POST',
    body: JSON.stringify(data),
  });

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
  const response = await fetch(`${API_BASE}/api/assessments/${assessmentId}/report`, {
    headers: authHeaders,
  });
  if (!response.ok) {
    throw new Error('Failed to download report');
  }
  return response.blob();
};
