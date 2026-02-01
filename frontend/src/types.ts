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
  llm_status?: 'pending' | 'completed' | 'failed';
  framework_mapping?: FrameworkMapping;
  detailed_roadmap?: DetailedRoadmap;
  analytics?: AnalyticsSummary;
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

// Enrichment types
export interface EnrichmentResult {
  company_name: string;
  industry: string;
  title?: string;
  description?: string;
  keywords?: string[];
  employees?: string;
  revenue?: string;
  location?: string;
  source_url?: string;
  confidence?: number;
  baseline_suggestion?: string;
}

// Organization with enrichment fields
export interface OrganizationWithEnrichment extends Organization {
  website_url?: string;
  org_profile?: string;
}

// Framework refs - unified type with id and name format (for ref.id/ref.name access)
export interface FrameworkRef {
  id: string;
  name: string;
  url?: string;
  ig_level?: number;  // For CIS controls
  tactic?: string;    // For MITRE ATT&CK
}

export interface FrameworkMappedFinding extends FindingSummary {
  finding_id?: string;
  mitre_refs?: FrameworkRef[];
  cis_refs?: FrameworkRef[];
  owasp_refs?: FrameworkRef[];
}

// Framework mapping structure with coverage stats
export interface FrameworkCoverage {
  mitre_techniques_total: number;
  cis_controls_total: number;
  owasp_total: number;
  ig1_coverage_pct?: number;
  ig2_coverage_pct?: number;
  ig3_coverage_pct?: number;
}

export interface FrameworkMapping {
  findings: FrameworkMappedFinding[];
  coverage?: FrameworkCoverage;
}

// Detailed roadmap types
export interface RoadmapMilestone {
  week: number;
  description: string;
  deliverable?: string;
}

export interface DetailedRoadmapItem {
  id?: string;
  title: string;
  action?: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  severity?: 'critical' | 'high' | 'medium' | 'low';
  phase: '30' | '60' | '90';
  status?: 'not_started' | 'in_progress' | 'completed' | 'todo';
  owner?: string;
  effort_estimate?: string;
  effort?: string;
  dependencies?: string[];
  milestones?: string[];  // Simple strings for display
  success_criteria?: string;
  domain?: string;
  finding_id?: string;
}

// Detailed roadmap wrapper with phases structure
export interface DetailedRoadmapPhase {
  title: string;
  items: DetailedRoadmapItem[];
}

export interface DetailedRoadmap {
  phases: DetailedRoadmapPhase[];
  summary?: string;
}

// Analytics types
export interface AttackStep {
  step?: number;
  action: string;
  technique_id?: string;
}

export interface AttackPath {
  id: string;
  name: string;
  description?: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  steps: AttackStep[];
  techniques?: Array<{ id: string; name: string }>;
  enabling_gaps: string[];
  likelihood?: number;
  impact?: number;
}

// Gap analysis types
export interface GapCategory {
  name: string;
  gaps: string[];
  severity?: 'critical' | 'high' | 'medium' | 'low';
}

export interface GapAnalysis {
  categories: GapCategory[];
  total_gaps?: number;
}

export interface RiskSummary {
  overall_risk_level: 'critical' | 'high' | 'medium' | 'low';
  key_risks: string[];
  mitigating_factors?: string[];
}

export interface AnalyticsSummary {
  attack_paths: AttackPath[];
  risk_distribution: Record<string, number>;
  top_risks: string[];
  improvement_recommendations: string[];
  detection_gaps?: GapAnalysis;
  response_gaps?: GapAnalysis;
  identity_gaps?: GapAnalysis;
  risk_summary?: RiskSummary;
}

// Tracker item for roadmap tracking
export interface TrackerItem {
  id: string;
  assessment_id: string;
  title: string;
  phase: '30' | '60' | '90';
  status: 'not_started' | 'in_progress' | 'completed' | 'done' | 'todo';
  priority: 'critical' | 'high' | 'medium' | 'low';
  owner?: string;
  due_date?: string;
  notes?: string;
  effort?: string;
  created_at: string;
  updated_at?: string;
}

// Roadmap API response wrapper
export interface RoadmapResponse {
  items: TrackerItem[];
  total?: number;
}

// Score trend for historical tracking
export interface ScoreTrendPoint {
  date: string;
  score: number;
  assessment_id: string;
  name?: string;  // Optional label for the data point
}
