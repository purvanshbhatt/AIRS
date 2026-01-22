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

// ----- Framework Mapping Types -----

export interface MitreRef {
  id: string;      // e.g., "T1566"
  name: string;    // e.g., "Phishing"
  tactic: string;  // e.g., "Initial Access"
  url: string;
}

export interface CISRef {
  id: string;      // e.g., "CIS-4.1"
  name: string;    // e.g., "Establish and Maintain a Secure Configuration Process"
  ig_level: number; // Implementation Group: 1, 2, or 3
}

export interface OWASPRef {
  id: string;      // e.g., "A01:2021"
  name: string;    // e.g., "Broken Access Control"
}

export interface FrameworkMappedFinding {
  finding_id: string;
  title: string;
  severity: string;
  domain: string;
  mitre_refs: MitreRef[];
  cis_refs: CISRef[];
  owasp_refs: OWASPRef[];
  impact_score: number;
}

export interface FrameworkCoverage {
  mitre_techniques_enabled: number;
  mitre_techniques_total: number;
  mitre_coverage_pct: number;
  cis_controls_met: number;
  cis_controls_total: number;
  cis_coverage_pct: number;
  ig1_coverage_pct: number;
  ig2_coverage_pct: number;
  ig3_coverage_pct: number;
}

export interface FrameworkMapping {
  findings: FrameworkMappedFinding[];
  coverage?: FrameworkCoverage;
}

// ----- Analytics Types -----

export interface AttackPathStep {
  step: number;
  action: string;
  mitre_technique?: string;
}

export interface AttackPath {
  id: string;
  name: string;
  likelihood: 'high' | 'medium' | 'low';
  impact: 'high' | 'medium' | 'low';
  description: string;
  enabling_gaps: string[];
  steps: AttackPathStep[];
  mitigations: string[];
}

export interface GapItem {
  id: string;
  title: string;
  severity: string;
}

export interface GapCategory {
  category: string;
  category_name: string;
  status: 'gap' | 'partial' | 'covered';
  gaps: GapItem[];
  coverage_score: number;
}

export interface Analytics {
  attack_paths: AttackPath[];
  detection_gaps: GapCategory[];
  response_gaps: GapCategory[];
  identity_gaps: GapCategory[];
  top_risks: string[];
  recommended_priorities: string[];
}

// ----- Detailed Roadmap Types -----

export interface DetailedRoadmapItem {
  finding_id: string;
  title: string;
  action: string;
  effort: 'low' | 'medium' | 'high';
  severity: string;
  domain: string;
  owner: string;
  milestones: string[];
  success_criteria: string;
}

export interface RoadmapPhase {
  name: string;
  description: string;
  item_count: number;
  effort_hours: number;
  risk_reduction: number;
  items: DetailedRoadmapItem[];
}

export interface DetailedRoadmap {
  summary: {
    total_items: number;
    total_effort_hours: number;
    total_risk_reduction: number;
    critical_items: number;
    quick_wins: number;
  };
  phases: {
    day30: RoadmapPhase;
    day60: RoadmapPhase;
    day90: RoadmapPhase;
    beyond: RoadmapPhase;
  };
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
  // New: Detailed roadmap with milestones
  detailed_roadmap?: DetailedRoadmap;
  // New: Framework mapping (MITRE/CIS/OWASP)
  framework_mapping?: FrameworkMapping;
  // New: Derived analytics (attack paths, gaps)
  analytics?: Analytics;
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
