export type ReadinessStatus = 'safe_to_open' | 'action_needed' | 'action_required' | 'critical_risk' | 'unknown' | string;

export interface DailyReadinessReport {
  org_id: string;
  status: ReadinessStatus;
  clinic_health_pct: number;
  connector_health_pct: number;
  greeting: string;
  summary: string;
  timeline: TimelineEvent[];
  business_continuity: BusinessContinuity;
  passed_checks: ReadinessCheck[];
  failed_checks: ReadinessCheck[];
  warnings: ReadinessCheck[];
  unknowns: UnknownItem[];
  immediate_actions: ActionCard[];
  coverage: CoverageReport;
  connectors: ConnectorReadiness[];
  verification: VerificationContext;
  health_check?: HealthCheckContext;
  trend: ReadinessTrend;
  value: ValueSummary;
  generated_at: string;
}

/**
 * Timeline entry. The backend contract is {timestamp, icon, label, detail, source};
 * the older UI shape {time, category, event, type, impact} is still accepted so
 * bundled sample reports keep rendering. Use normalizeTimelineEvent() before display.
 */
export interface TimelineEvent {
  // backend contract
  timestamp?: string;
  icon?: 'check' | 'warning' | 'error' | 'info' | string;
  label?: string;
  detail?: string | null;
  source?: string;
  // legacy UI shape
  time?: string;
  category?: 'today' | 'yesterday' | 'last_week';
  event?: string;
  type?: 'verified' | 'action_taken' | 'alert' | 'update';
  impact?: string;
}

export interface NormalizedTimelineEvent {
  time: string;
  category: 'today' | 'yesterday' | 'last_week';
  event: string;
  type: 'verified' | 'action_taken' | 'alert' | 'update';
  impact?: string;
  source?: string;
}

export function normalizeTimelineEvent(e: TimelineEvent, now: Date = new Date()): NormalizedTimelineEvent {
  const iso = e.timestamp || e.time || now.toISOString();
  const when = new Date(iso);
  const ageHours = Math.max(0, (now.getTime() - when.getTime()) / 36e5);
  const category: NormalizedTimelineEvent['category'] =
    e.category || (ageHours < 24 ? 'today' : ageHours < 48 ? 'yesterday' : 'last_week');
  const iconType: Record<string, NormalizedTimelineEvent['type']> = {
    check: 'verified', warning: 'alert', error: 'alert', info: 'update',
  };
  const type: NormalizedTimelineEvent['type'] = e.type || iconType[e.icon || ''] || 'update';
  return {
    time: Number.isNaN(when.getTime()) ? iso : when.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }),
    category,
    event: e.event || e.label || 'Update',
    type,
    impact: e.impact ?? (e.detail || undefined),
    source: e.source,
  };
}

export interface OperationalReadiness {
  can_operate_today: boolean;
  can_recover: boolean;
  current_blockers: string[];
  estimated_downtime_minutes: number;
  critical_systems_verified: string[];
  critical_systems_assumed: string[];
}

export interface BusinessContinuity {
  safe_to_operate?: boolean;
  executive_verdict?: string;
  rto_estimate_minutes?: number;
  rpo_status?: string;
  operational_readiness: OperationalReadiness;
}

export interface ExecutiveExplanation {
  status: string;
  business_label: string;
  technical_label: string;
  what_it_means: string;
  why_it_matters: string;
  what_to_do_next: string;
  evidence_state: string;
  last_verified_at: string;
}

export interface ReadinessCheck {
  id: string;
  name: string;
  category: string;
  description?: string;
  explanation?: ExecutiveExplanation;
}

export interface UnknownItem {
  system: string;
  reason: string;
  last_known_state?: string;
  impact_on_readiness?: string;
}

export interface ActionCard {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  impact_narrative: string;
  evidence: string;
  recommendation: string;
  can_be_undone: boolean;
  last_verified_at: string;
  confidence_pct: number;
  verification_method: string;
  fix_now_available?: boolean;
  explanation?: ExecutiveExplanation;
}

export interface CoverageArea {
  name: string;
  monitored_items: number;
  unmonitored_items: number;
  percentage: number;
}

export interface CoverageReport {
  overall_percentage: number;
  areas: CoverageArea[];
}

export interface ConnectorReadiness {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  last_sync: string;
}

export interface HealthCheckExplanation {
  method: string;
  timestamp: string;
  confidence: number;
}

export type VerificationExplanation = HealthCheckExplanation;

export interface HealthCheckContext {
  overall_confidence_pct: number;
  verified_items_count: number;
  total_items_count: number;
  explanations?: Record<string, HealthCheckExplanation>;
}

export type VerificationContext = HealthCheckContext;

export interface ReadinessTrend {
  direction: 'up' | 'down' | 'flat';
  percentage_change: number;
  narrative: string;
}

export interface ValueSummary {
  roi_metrics?: Record<string, number | string>;
  hours_saved?: number;
}
