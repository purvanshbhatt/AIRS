/**
 * Typed contracts for ResilAI Report Center Backend Integration & History Management.
 * Sourced from backend schema contracts and executive Stitch design language.
 */

export type ReportType =
  | 'board_story'
  | 'monthly_ops'
  | 'hipaa_audit'
  | 'technical_telemetry'
  | 'executive_pdf'
  | string;

export type ReportFormat = 'pdf' | 'json' | 'csv';

export type ReportGenerationStatus = 'ready' | 'generating' | 'failed' | 'idle';

export interface GenerateReportRequest {
  organization_id: string;
  report_type: 'board_story' | 'monthly_ops' | 'hipaa_audit' | 'technical_telemetry' | string;
  format?: ReportFormat;
  title?: string;
  assessment_id?: string;
  parameters?: {
    include_evidence?: boolean;
    include_telemetry?: boolean;
    period_days?: number;
    target_frameworks?: string[];
    [key: string]: unknown;
  };
}

export interface GenerateReportResponse {
  id: string;
  report_id?: string;
  status: ReportGenerationStatus;
  progress?: number;
  message?: string;
  download_url?: string;
  created_at: string;
  estimated_seconds?: number;
}

export interface BackendReport {
  id: string;
  owner_uid?: string;
  organization_id: string;
  organization_name?: string;
  assessment_id?: string;
  assessment_title?: string;
  report_type: ReportType;
  title: string;
  format?: ReportFormat;
  status?: ReportGenerationStatus;
  file_size_bytes?: number;
  file_size_formatted?: string;
  overall_score?: number;
  maturity_level?: number;
  maturity_name?: string;
  findings_count?: number;
  critical_high_count?: number;
  created_at: string;
  updated_at?: string;
  download_url?: string;
  summary_text?: string;
}

export interface ReportListResponse {
  reports: BackendReport[];
  total: number;
}

export interface ReportFilters {
  organization_id?: string;
  assessment_id?: string;
  report_type?: ReportType;
  format?: ReportFormat;
  status?: ReportGenerationStatus;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface DomainScoreSnapshot {
  domain_id: string;
  domain_name: string;
  score: number;
  score_5?: number;
  weight?: number;
  earned_points?: number;
  max_points?: number;
}

export interface FindingSnapshot {
  id: string;
  title: string;
  severity: string;
  domain?: string;
  evidence?: string;
  recommendation?: string;
  description?: string;
}

export interface ReportSnapshot {
  assessment_id?: string;
  assessment_title?: string;
  organization_id?: string;
  organization_name?: string;
  overall_score: number;
  maturity_level: number;
  maturity_name: string;
  domain_scores: DomainScoreSnapshot[];
  findings: FindingSnapshot[];
  findings_count: number;
  critical_high_count?: number;
  baseline_selected?: string;
  executive_summary?: string;
  roadmap_narrative?: string;
  rubric_version?: string;
  generated_at: string;
}

export interface ReportDetail extends BackendReport {
  snapshot: ReportSnapshot;
}

// Backward-compatible alias for existing frontend references
export type Report = BackendReport;
