// API Types for AIRS

export interface Organization {
  id: string;
  name: string;
  industry?: string;
  size?: string;
  integration_status?: string;
  analytics_enabled?: boolean;
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
  // NIST CSF 2.0 mapping (v2.0)
  nist_function?: string;   // e.g. "DE", "PR", "RS", "RC"
  nist_category?: string;   // e.g. "DE.CM-1", "PR.AA-5"
  // SIEM verification status (v0.3-enterprise)
  verification_status?: 'SELF_REPORTED' | 'VERIFIED' | 'PENDING';
  verification_source?: string;  // e.g., "Splunk", "Microsoft Sentinel"
}

export interface AssessmentSummary {
  api_version: string;
  product?: ProductInfo;
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
  // Enterprise roadmap fields (v2.0)
  timeline_label?: string;  // e.g. "Immediate", "Near-term", "Strategic"
  risk_impact?: string;     // e.g. "Critical Risk Reduction", "High Impact"
  nist_category?: string;   // e.g. "DE.CM-1", "PR.AA-5"
}

// Detailed roadmap wrapper with phases structure
export interface DetailedRoadmapPhase {
  title: string;
  name?: string;  // Display name e.g. "Immediate (0–30 Days)"
  description?: string;
  item_count?: number;
  effort_hours?: number;
  items: DetailedRoadmapItem[];
}

export interface DetailedRoadmapSummary {
  total_items: number;
  day30_count: number;
  day60_count: number;
  day90_count: number;
  critical_items?: number;
  quick_wins?: number;
  total_effort_hours?: number;
  total_risk_reduction?: string;
  by_priority?: Record<string, number>;
  by_effort?: Record<string, number>;
  generated_at?: string;
}

export interface DetailedRoadmap {
  phases: Record<string, DetailedRoadmapPhase>;  // Keyed by "day30", "day60", "day90"
  summary?: DetailedRoadmapSummary;
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
  category?: string;
  gaps: string[];
  gap_count?: number;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  is_critical?: boolean;
  description?: string;
  findings?: Array<{ title: string }>;
}

export interface GapAnalysis {
  categories: GapCategory[];
  total_gaps?: number;
}

export interface RiskSummary {
  overall_risk_level: 'critical' | 'high' | 'medium' | 'low';
  key_risks: string[];
  mitigating_factors?: string[];
  attack_paths_enabled?: number;
  total_gaps_identified?: number;
  severity_counts?: Record<string, number>;
  findings_count?: number;
  total_risk_score?: number;
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
  // Enterprise analytics contract fields (v2.0)
  gap_category?: string;    // Primary gap category label
  maturity_tier?: string;   // e.g. "Initial", "Developing", "Defined", "Managed", "Optimized"
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

// Integration types
export interface ApiKeyMetadata {
  id: string;
  org_id: string;
  prefix: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used_at?: string | null;
}

export interface ApiKeyCreateResponse {
  id: string;
  org_id: string;
  prefix: string;
  scopes: string[];
  api_key: string;
  created_at: string;
}

export interface Webhook {
  id: string;
  org_id: string;
  url: string;
  event_types: string[];
  is_active: boolean;
  created_at: string;
}

export interface ExternalFinding {
  id: string;
  org_id: string;
  source: string;
  title: string;
  severity: string;
  created_at: string;
  raw_json: Record<string, unknown>;
}

export interface WebhookUrlTestResponse {
  delivered: boolean;
  status_code?: number;
  error?: string;
  event_type: string;
  payload: Record<string, unknown>;
}

export interface ProductInfo {
  name: string;
  version?: string | null;
}

export interface SystemStatus {
  version?: string | null;
  environment: string;
  llm_enabled: boolean;
  demo_mode: boolean;
  integrations_enabled: boolean;
  last_deployment_at?: string | null;
}

export interface AuditEvent {
  id: string;
  org_id: string;
  action: string;
  actor: string;
  timestamp: string;
}

export interface PilotRequestInput {
  company_name: string;
  team_size: string;
  current_security_tools?: string;
  email: string;
}

// Enterprise Pilot Lead (Phase 6 — extended form for /api/v1/pilot-leads)
export interface EnterprisePilotLeadInput {
  company_name: string;
  contact_name: string;
  email: string;
  industry?: string;
  company_size?: string;
  team_size?: string;
  current_security_tools?: string;
  ai_usage_description?: string;
  current_siem_provider?: string;
}

// Methodology endpoint response (Phase 4)
export interface MethodologyDomain {
  domain_id: string;
  domain_name: string;
  weight_pct: number;
  nist_function?: string;
  nist_function_name?: string;
  nist_categories?: string[];
  description: string;
  question_count: number;
  max_domain_score: number;
}

export interface MethodologyResponse {
  rubric_version: string;
  nist_csf_version: string;
  methodology_basis: string[];
  total_weight: number;
  max_domain_score: number;
  scoring_formula: string;
  domains: MethodologyDomain[];
  maturity_levels: Record<string, unknown>;
  remediation_timelines: Record<string, unknown>;
}

export interface SiemExportFinding {
  severity: string;
  category?: string;
  title: string;
  description?: string;
  mitre_refs: Array<Record<string, unknown>>;
  cis_refs: Array<Record<string, unknown>>;
  owasp_refs: Array<Record<string, unknown>>;
  remediation?: string;
}

export interface SiemExportPayload {
  organization?: string;
  assessment_id: string;
  score: number;
  generated_at: string;
  findings: SiemExportFinding[];
}

// =============================================================================
// Question Suggestions
// =============================================================================

export interface SuggestedQuestion {
  id: string;
  question_text: string;
  domain_id: string;
  framework_tags: string[];
  maturity_level: 'basic' | 'managed' | 'advanced';
  effort_level: 'low' | 'medium' | 'high';
  impact_level: 'low' | 'medium' | 'high';
  control_function: 'govern' | 'identify' | 'protect' | 'detect' | 'respond' | 'recover';
}

export interface SuggestionsResponse {
  suggestions: SuggestedQuestion[];
  total_count: number;
  org_maturity: string | null;
  weakest_functions: string[] | null;
}
