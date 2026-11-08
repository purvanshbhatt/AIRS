import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Building, CheckCheck, Plug, ListChecks, FileText } from 'lucide-react';
import { getDailyReadinessReport, triggerProblemFix } from '../../api';
import type { DailyReadinessReport, ActionCard } from '../../types/readiness';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import { FirstRunChecklist } from '../../components/readiness/FirstRunChecklist';
import {
  derivePlainVerdict,
  verdictToneClass,
  TechnicalDetails,
  ConnectFirstEmptyState,
} from '../../components/readiness/PlainLanguage';
import { BriefHeader } from '../../components/readiness/v2/BriefHeader';
import { ReadinessRing } from '../../components/readiness/v2/ReadinessRing';
import { StatusRow, deriveAreaStatuses } from '../../components/readiness/v2/StatusRow';
import { AttentionCard } from '../../components/readiness/v2/AttentionCard';
import { OvernightStrip } from '../../components/readiness/v2/OvernightStrip';

/**
 * Morning brief, V2 (staging preview).
 *
 * Same data as TodayPage (getDailyReadinessReport, useActiveOrg, the
 * PlainLanguage helpers); only the presentation changes. Every number on
 * this page is read from the report. Opt out at any time with the
 * "Switch to classic view" link, which sets resilai_dashboard_v2 = 'false'.
 */

export const DASHBOARD_V2_FLAG = 'resilai_dashboard_v2';

/** Mirrors TodayPage: a fresh org with no evidence renders as "unknown", not as an error. */
function emptyReport(orgId: string): DailyReadinessReport {
  return {
    org_id: orgId,
    date: new Date().toISOString(),
    status: 'unknown',
    clinic_health_pct: 0,
    connector_health_pct: 0,
    greeting: 'Welcome to ResilAI',
    summary: 'No active telemetry connectors are currently providing evidence.',
    verified_controls_count: 0,
    total_controls_count: 5,
    evidence_count: 0,
    confidence_level: 'none',
    questions: [],
    immediate_actions: [],
    passed_checks: [],
    failed_checks: [],
    warnings: [],
    unknowns: [],
    connectors: [],
    timeline: [],
    business_continuity: {
      operational_readiness: {
        can_operate_today: false,
        can_recover: false,
        current_blockers: ['No security systems connected'],
        estimated_downtime_minutes: 0,
        critical_systems_verified: [],
        critical_systems_assumed: [],
      },
    },
    coverage: { overall_percentage: 0, areas: [] },
    verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 5 },
    trend: { direction: 'flat', percentage_change: 0, narrative: 'Awaiting initial telemetry connection to establish baseline.' },
    value: { hours_saved: 0 },
    generated_at: new Date().toISOString(),
  } as unknown as DailyReadinessReport;
}

function switchToClassicView() {
  try {
    localStorage.setItem(DASHBOARD_V2_FLAG, 'false');
  } catch {
    /* storage unavailable: still reload so the user is not stuck */
  }
  window.location.reload();
}

function ClassicViewLink() {
  return (
    <p className="text-center text-xs text-on-surface-variant">
      Prefer the previous layout?{' '}
      <button
        type="button"
        onClick={switchToClassicView}
        className="font-semibold text-ready-emerald hover:underline cursor-pointer"
        data-testid="switch-to-classic"
      >
        Switch to classic view
      </button>
    </p>
  );
}

export default function TodayPageV2() {
  const { orgId, orgName, hasOrg, isDemo, loading: orgLoading } = useActiveOrg();
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fixingId, setFixingId] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  const loadReport = async () => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getDailyReadinessReport(orgId);
      setReport(data);
    } catch (err: any) {
      console.warn('[TodayPageV2] Daily report fetch notice:', err);
      const errMsg = String(err?.message || '').toLowerCase();
      if (errMsg.includes('not found') || errMsg.includes('404') || errMsg.includes('unable to reach') || errMsg.includes('access')) {
        setReport(emptyReport(orgId));
      } else {
        setError(err?.message || 'Failed to load readiness data');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orgId) {
      loadReport();
    } else if (!orgLoading) {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, orgLoading]);

  const handleFix = async (problemId: string) => {
    setFixingId(problemId);
    try {
      const res = await triggerProblemFix(problemId);
      if (isDemo || res?.simulated) {
        // Sandbox: same optimistic update as the classic view so the demo stays coherent.
        setReport(prev => {
          if (!prev) return prev;
          const remaining = (prev.immediate_actions || []).filter(
            (a: any) => (a.id || a.action_id) !== problemId
          );
          const newScore = Math.min(100, (prev.clinic_health_pct || 74) + 8);
          return {
            ...prev,
            clinic_health_pct: newScore,
            status: newScore >= 90 ? 'safe_to_open' : 'action_required',
            immediate_actions: remaining,
          };
        });
      } else {
        await loadReport();
      }
    } catch (err) {
      console.error('Fix failed:', err);
    } finally {
      setFixingId(null);
    }
  };

  if (orgLoading || loading) return <LoadingState />;

  // No organization yet (real user): point to onboarding.
  if (!hasOrg && !isDemo) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6 animate-fade-up" data-testid="today-v2">
        <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-8 sm:p-10 text-center space-y-5 m3-elevation-2">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center">
            <Building className="w-7 h-7 text-ready-emerald" aria-hidden="true" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-on-surface tracking-tight">Set up your readiness workspace</h1>
          <p className="text-sm text-on-surface-variant max-w-md mx-auto leading-relaxed">
            Create an organization to establish continuous evidence collection and deterministic readiness scoring.
          </p>
          <Link
            to="/onboarding?new=true"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-ready-emerald text-slate-950 text-sm font-bold rounded-xl hover:bg-ready-emerald/90 transition-all active:scale-[0.98]"
          >
            <Building className="w-4 h-4" aria-hidden="true" />
            <span>Create Organization</span>
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
        <ClassicViewLink />
      </div>
    );
  }

  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  const plain = derivePlainVerdict(report);
  const isUnknown = plain.tone === 'unknown';
  const actions: ActionCard[] = report.immediate_actions || [];

  // Real org, nothing connected: one calm empty state, no invented score.
  if (isUnknown && !isDemo) {
    return (
      <div className="max-w-5xl mx-auto space-y-8 pb-24 animate-fade-up" data-testid="today-v2">
        <BriefHeader orgName={orgName} date={report.generated_at} />
        <section className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 sm:p-10 text-center space-y-3 m3-elevation-1">
          <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">Not yet verified</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-on-surface max-w-2xl mx-auto" data-testid="plain-verdict">
            {plain.verdict}
          </h2>
          <p className={`text-sm sm:text-base font-semibold ${verdictToneClass[plain.tone]}`} data-testid="plain-today">
            {plain.today}
          </p>
        </section>
        <FirstRunChecklist orgId={orgId} report={report} isDemo={isDemo} />
        <ConnectFirstEmptyState />
        <ClassicViewLink />
      </div>
    );
  }

  const areas = deriveAreaStatuses(report);
  const verifiedCount = report.verification?.verified_items_count;
  const totalCount = report.verification?.total_items_count;
  const hasCheckCounts = typeof verifiedCount === 'number' && typeof totalCount === 'number' && totalCount > 0;
  const confidencePct = report.verification?.overall_confidence_pct ?? 0;
  const heroBorder = {
    ready: 'border-t-ready-emerald/50',
    warning: 'border-t-drift-amber/50',
    critical: 'border-t-critical-red/50',
    unknown: 'border-t-outline-variant',
  }[plain.tone];

  const fadeIn = reduceMotion
    ? {}
    : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.35, ease: 'easeOut' as const } };

  return (
    <div className="max-w-6xl mx-auto space-y-8 sm:space-y-10 pb-24" data-testid="today-v2">
      <ContextualDemoBanner section="today" />

      <BriefHeader orgName={orgName} date={report.generated_at} isDemo={isDemo} />

      {/* Hero: verdict, ring, today line, one action */}
      <motion.section
        {...fadeIn}
        className={`bg-surface-container-low rounded-2xl border border-surface-bright border-t-2 ${heroBorder} p-6 sm:p-10 m3-elevation-2`}
        aria-labelledby="v2-verdict"
      >
        <div className="flex flex-col-reverse lg:flex-row lg:items-center gap-8 lg:gap-12">
          <div className="flex-1 min-w-0 text-center lg:text-left">
            <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mb-3">
              Today&apos;s verdict
            </p>
            <h2
              id="v2-verdict"
              className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-on-surface leading-tight max-w-2xl mx-auto lg:mx-0"
              data-testid="plain-verdict"
            >
              {plain.verdict}
            </h2>
            <p
              className={`mt-4 text-base sm:text-lg font-semibold leading-snug max-w-2xl mx-auto lg:mx-0 ${verdictToneClass[plain.tone]}`}
              data-testid="plain-today"
            >
              {plain.today}
            </p>
            {hasCheckCounts && (
              <p className="mt-3 text-sm text-on-surface-variant">
                {verifiedCount} of {totalCount} checks passed using live data from your systems.
              </p>
            )}
            <div className="mt-6 flex flex-wrap items-center justify-center lg:justify-start gap-3">
              {actions.length > 0 ? (
                <a
                  href="#v2-attention"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 transition-colors"
                  data-testid="primary-action"
                >
                  <ListChecks className="w-4 h-4" aria-hidden="true" />
                  Start with the first item ({actions.length})
                </a>
              ) : (
                <Link
                  to="/reports"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 transition-colors"
                  data-testid="primary-action"
                >
                  <FileText className="w-4 h-4" aria-hidden="true" />
                  Export today&apos;s report
                </Link>
              )}
              <span className="text-xs text-on-surface-variant">Checked around the clock. We tell you if this changes.</span>
            </div>
          </div>
          <div className="flex justify-center lg:justify-end">
            <ReadinessRing score={isUnknown ? null : report.clinic_health_pct ?? 0} tone={plain.tone} />
          </div>
        </div>
      </motion.section>

      <FirstRunChecklist orgId={orgId} report={report} isDemo={isDemo} />

      {/* Three areas a director asks about */}
      <StatusRow areas={areas} />

      {/* What needs attention */}
      <section id="v2-attention" className="space-y-4 scroll-mt-24" aria-labelledby="v2-attention-title">
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 id="v2-attention-title" className="text-lg sm:text-xl font-bold tracking-tight text-on-surface">What needs attention</h2>
            <p className="text-sm text-on-surface-variant mt-0.5">
              {actions.length === 0 ? 'Nothing is waiting on you or your IT provider.' : `${actions.length} item${actions.length === 1 ? '' : 's'}, most urgent first.`}
            </p>
          </div>
          {actions.length > 3 && (
            <Link to="/needs-attention" className="text-xs font-semibold text-ready-emerald hover:underline inline-flex items-center gap-1 shrink-0">
              See all {actions.length}
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </Link>
          )}
        </div>

        {actions.length === 0 ? (
          <div className="bg-surface-container-low border border-dashed border-surface-bright rounded-2xl p-8 text-center" data-testid="attention-empty">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald mb-3">
              <CheckCheck className="w-6 h-6" aria-hidden="true" />
            </div>
            <p className="text-base font-bold text-on-surface">Every protection we check passed overnight</p>
            <p className="text-sm text-on-surface-variant mt-1 max-w-md mx-auto leading-relaxed">
              We keep checking around the clock and will tell you if that changes.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {actions.slice(0, 3).map((action, index) => (
              <AttentionCard
                key={`${action.id || index}`}
                action={action}
                index={index}
                fixing={fixingId === (action.id || (action as any).action_id)}
                onFix={handleFix}
              />
            ))}
          </div>
        )}
      </section>

      <OvernightStrip report={report} />

      <TechnicalDetails title="Technical details" hint="connected systems, check counts" defaultOpen={false}>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Connected systems health</span>
            <span className="font-mono font-semibold text-on-surface">{report.connector_health_pct ?? 0}%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Checks verified</span>
            <span className="font-mono font-semibold text-on-surface">{hasCheckCounts ? `${verifiedCount}/${totalCount}` : 'n/a'}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Confidence</span>
            <span className="font-mono font-semibold text-on-surface">{confidencePct}%</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] font-mono uppercase tracking-wider text-on-surface-variant border-b border-surface-bright/40">
                <th className="py-2 pr-3 font-semibold">Connected system (connector)</th>
                <th className="py-2 pr-3 font-semibold">Status</th>
                <th className="py-2 font-semibold">Last sync</th>
              </tr>
            </thead>
            <tbody>
              {(report.connectors || []).length === 0 ? (
                <tr>
                  <td colSpan={3} className="py-3 text-on-surface-variant italic">No connected systems reported.</td>
                </tr>
              ) : (
                (report.connectors || []).map(c => (
                  <tr key={c.name} className="border-b border-surface-bright/30 last:border-0">
                    <td className="py-2 pr-3 font-semibold text-on-surface">{c.name}</td>
                    <td className={`py-2 pr-3 font-mono ${c.status === 'healthy' ? 'text-ready-emerald' : c.status === 'degraded' ? 'text-drift-amber' : 'text-critical-red'}`}>
                      {c.status}
                    </td>
                    <td className="py-2 font-mono text-on-surface-variant">{c.last_sync}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-on-surface-variant/70">
          Report generated {report.generated_at}. Proof hashes (SHA-256) for each check are in the Audit Vault.
        </p>
        <Link to="/connectors" className="inline-flex items-center gap-1.5 text-xs font-semibold text-ready-emerald hover:underline">
          <Plug className="w-3.5 h-3.5" aria-hidden="true" />
          Manage connected systems
        </Link>
      </TechnicalDetails>

      <ClassicViewLink />
    </div>
  );
}
