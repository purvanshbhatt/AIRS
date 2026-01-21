// API Types for AIRS

export interface Organization {
  id: string;
  name: string;
  industry?: string;
  size?: string;
  created_at: string;
}

export interface Assessment {
  id: string;
  organization_id: string;
  organization_name?: string;
  title: string;
  version: string;
  status: string;
  overall_score?: number;
  maturity_level?: number;
  maturity_name?: string;
  created_at: string;
}

export interface Question {
  id: string;
  text: string;
  type: 'boolean' | 'percentage' | 'numeric';
  points: number;
  thresholds?: Record<string, number>;
}

export interface Domain {
  name: string;
  description: string;
  weight: number;
  questions: Question[];
  scoring_formula?: string;
}

export interface Rubric {
  version: string;
  total_weight: number;
  max_domain_score: number;
  domains: Record<string, Domain>;
}

export interface DomainScore {
  domain_id: string;
  domain_name: string;
  score: number;
  weight: number;
  earned_points?: number;
  max_points?: number;
}

export interface Finding {
  id?: string;
  rule_id?: string;
  title: string;
  severity: string;
  evidence?: string;
  recommendation?: string;
  domain?: string;
  domain_name?: string;
  description?: string;
  reference?: string;
}

export interface ScoreResult {
  overall_score: number;
  maturity_level: number;
  maturity_name: string;
  domains: DomainScore[];
  findings_count: number;
}

export interface AssessmentDetail extends Assessment {
  answers: Array<{ question_id: string; value: string | number | boolean }>;
  scores: DomainScore[];
  domain_scores?: DomainScore[];
  findings: Finding[];
}

// Summary types for executive dashboard

export interface RoadmapItem {
  title: string;
  action: string;
  severity: string;
  domain?: string;
}

export interface Roadmap {
  day30: RoadmapItem[];
  day60: RoadmapItem[];
  day90: RoadmapItem[];
}

export interface ReadinessTier {
  label: 'Critical' | 'Needs Work' | 'Good' | 'Strong';
  min_score: number;
  max_score: number;
  color: 'danger' | 'warning' | 'primary' | 'success';
}

export interface DomainScoreSummary {
  domain_id: string;
  domain_name: string;
  score: number;      // Percentage (0-100)
  score_5: number;    // 0-5 scale
  weight: number;
  earned_points?: number;
  max_points?: number;
}

export interface FindingSummary {
  id: string;
  title: string;
  severity: string;
  domain?: string;
  evidence?: string;
  recommendation?: string;
  description?: string;
}

export interface AssessmentSummary {
  api_version: string;
  id: string;
  title?: string;
  organization_id: string;
  organization_name?: string;
  created_at: string;
  completed_at?: string;
  status: string;
  overall_score: number;
  tier: ReadinessTier;
  domain_scores: DomainScoreSummary[];
  findings: FindingSummary[];
  findings_count: number;
  critical_high_count: number;
  roadmap: Roadmap;
  executive_summary: string;
  executive_summary_text?: string;
  roadmap_narrative_text?: string;
  baselines_available?: string[];
  baseline_profiles?: Record<string, Record<string, number>>;
  // LLM metadata (informational only - does NOT affect scoring)
  llm_enabled?: boolean;
  llm_provider?: string | null;
  llm_model?: string | null;
  llm_mode?: 'demo' | 'prod' | 'disabled';
}

// Standardized API error response
export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}

// Report type for saved reports library
export interface Report {
  id: string;
  owner_uid: string;
  assessment_id: string;
  assessment_title?: string;
  organization_id: string;
  organization_name?: string;
  report_type: string;
  title: string;
  overall_score?: number;
  maturity_level?: number;
  maturity_name?: string;
  findings_count?: number;
  created_at: string;
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
}

export interface ReportSnapshot {
  assessment_id: string;
  assessment_title?: string;
  organization_id: string;
  organization_name?: string;
  overall_score: number;
  maturity_level: number;
  maturity_name: string;
  domain_scores: Array<{
    domain_id: string;
    domain_name: string;
    score: number;
    score_5: number;
    weight: number;
  }>;
  findings: Array<{
    id: string;
    title: string;
    severity: string;
    domain?: string;
    recommendation?: string;
  }>;
  findings_count: number;
  critical_high_count: number;
  executive_summary?: string;
  roadmap_narrative?: string;
  generated_at: string;
}

export interface ReportDetail extends Report {
  snapshot: ReportSnapshot;
}

// Dashboard KPI types
export interface DashboardStats {
  total_organizations: number;
  total_assessments: number;
  completed_assessments: number;
  draft_assessments: number;
  average_score?: number;
  recent_assessments: Assessment[];
}
