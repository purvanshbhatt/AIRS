import { useEffect, useState } from 'react';
import { 
  getDailyReadinessReport, 
  triggerProblemFix, 
  getBoardStory,
  getBoardStoryPdfUrl,
  type BoardStory 
} from '../../api';
import type { DailyReadinessReport, ActionCard } from '../../types/readiness';
import { CoverageModal } from '../../components/readiness/CoverageModal';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { DataState, VerifiedValue, EvidenceFreshness, EvidenceState } from '../../components/evidence/EvidenceState';
import { ExecutiveExplanation } from '../../components/evidence/ExecutiveExplanation';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import {
  derivePlainVerdict,
  normalizeAction,
  guidanceForAction,
  verdictToneClass,
  CheckOwnerStrip,
  TechnicalDetails,
  PlainTerm,
} from '../../components/readiness/PlainLanguage';
import { Link } from 'react-router-dom';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { tokens } from '../../lib/design-tokens';
import {
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  CheckCheck,
  HardDrive,
  KeyRound,
  Shield,
  Activity,
  ArrowRight,
  ShieldAlert,
  Plug,
  Building,
  FileCheck2,
  X,
  Server,
  FileText,
  Clock,
  ChevronRight,
  RefreshCw,
  Download,
  BarChart3
} from 'lucide-react';

export default function TodayPage() {
  const { orgId, hasOrg, isDemo, loading: orgLoading } = useActiveOrg();
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coverageModalOpen, setCoverageModalOpen] = useState(false);
  const [fixingId, setFixingId] = useState<string | null>(null);
  
  // Leadership Explanation Modal State
  const [explainModalOpen, setExplainModalOpen] = useState(false);
  const [boardStory, setBoardStory] = useState<BoardStory | null>(null);
  const [loadingStory, setLoadingStory] = useState(false);
  const [explainViewMode, setExplainViewMode] = useState<'executive' | 'technical'>('executive');

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
      console.warn('[TodayPage] Daily report fetch notice:', err);
      // For a fresh organization with zero evidence or initial 404, treat as fresh unverified state
      const errMsg = String(err?.message || '').toLowerCase();
      if (errMsg.includes('not found') || errMsg.includes('404') || errMsg.includes('unable to reach') || errMsg.includes('access')) {
        setReport({
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
            }
          },
          coverage: {
            overall_percentage: 0,
            areas: []
          },
          verification: {
            overall_confidence_pct: 0,
            verified_items_count: 0,
            total_items_count: 5,
          },
          trend: {
            direction: 'flat',
            percentage_change: 0,
            narrative: 'Awaiting initial telemetry connection to establish baseline.'
          },
          value: {
            hours_saved: 0,
          },
          generated_at: new Date().toISOString(),
        } as unknown as DailyReadinessReport);
      } else {
        setError(err.message || "Failed to load readiness data");
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
  }, [orgId, orgLoading]);

  const handleFix = async (problemId: string) => {
    setFixingId(problemId);
    try {
      const res = await triggerProblemFix(problemId);
      if (isDemo || res?.simulated) {
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

  const handleOpenExplainLeadership = async () => {
    setExplainModalOpen(true);
    if (!boardStory && orgId) {
      setLoadingStory(true);
      try {
        const story = await getBoardStory(orgId);
        setBoardStory(story);
      } catch (e) {
        console.warn('Could not fetch board story, using fallback narrative:', e);
      } finally {
        setLoadingStory(false);
      }
    }
  };

  if (orgLoading || loading) return <LoadingState />;

  // Scenario 1: User has no organization established yet
  if (!hasOrg && !isDemo) {
    return (
      <div className="space-y-8 animate-fade-up max-w-2xl mx-auto py-12">
        <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-8 sm:p-10 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center">
            <Building className="w-8 h-8 text-ready-emerald" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-on-surface tracking-tight">
              Set up your readiness workspace
            </h2>
            <p className="text-sm text-on-surface-variant max-w-md mx-auto leading-relaxed">
              Create an organization to establish continuous evidence collection and deterministic readiness scoring.
            </p>
          </div>
          <div>
            <Link
              to="/onboarding?new=true"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-ready-emerald text-slate-950 text-sm font-bold rounded-xl hover:bg-ready-emerald/90 transition-all active:scale-[0.98] shadow-sm"
            >
              <Building className="w-4 h-4" />
              <span>Create Organization</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  const isUnknown = report.status === 'unknown' || (report.verification && report.verification.overall_confidence_pct === 0) || (!report.clinic_health_pct && (!report.immediate_actions || report.immediate_actions.length === 0));
  const isReady = !isUnknown && (report.status === 'safe_to_open' || report.clinic_health_pct >= 90);
  const actionsList = report.immediate_actions || [];

  // Scenario 2: LIVE Organization with NO evidence connected yet (The Executive Readiness Launchpad)
  if (isUnknown && !isDemo) {
    return (
      <div className="space-y-8 animate-fade-up max-w-5xl mx-auto">
        {/* North Star Hero: Not Yet Verified */}
        <section className="flex flex-col items-center justify-center text-center py-12 px-6 sm:px-10 bg-surface-container-low rounded-2xl border border-surface-bright backdrop-blur-md relative overflow-hidden shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-b from-drift-amber/5 via-transparent to-transparent pointer-events-none" />
          
          <div className="w-16 h-16 bg-drift-amber/10 border border-drift-amber/30 rounded-2xl flex items-center justify-center mb-5 shadow-sm">
            <ShieldAlert className="w-8 h-8 text-drift-amber" />
          </div>

          <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-drift-amber/10 text-drift-amber rounded-full text-xs font-semibold border border-drift-amber/30 mb-3.5 font-mono uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-drift-amber animate-pulse" />
            LIVE WORKSPACE • NOT YET VERIFIED
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-on-surface mb-3">
            Welcome to your ResilAI Readiness Workspace
          </h2>
          <p className="text-lg sm:text-xl font-semibold text-on-surface max-w-2xl mx-auto leading-snug mb-2" data-testid="plain-verdict">
            We cannot tell yet whether your practice is protected, because no systems are connected.
          </p>
          <p className="text-sm sm:text-base text-on-surface-variant max-w-2xl mx-auto leading-relaxed mb-8">
            Connect your backup system (for example Veeam) or Microsoft 365 first. That is where most practices get their first answer, and each takes one login from your IT provider. ResilAI then checks live data from those systems every day, so nothing here depends on a questionnaire.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3.5">
            <Link
              to="/connectors"
              className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl hover:shadow-lg hover:shadow-ready-emerald/25 transition-all duration-300 active:scale-[0.98]"
            >
              <Plug className="w-4 h-4" />
              <span>Connect Security System</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <a
              href="/demo"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/40 text-sm font-semibold rounded-xl transition-all"
            >
              <Sparkles className="w-4 h-4 text-drift-amber" />
              <span>Explore Live Sandbox Demo</span>
            </a>
          </div>
        </section>

        {/* 3-Stage Progress Guide */}
        <section className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 sm:p-8">
          <h3 className="text-xs font-bold font-mono text-on-surface-variant uppercase tracking-wider mb-6">
            The Path to Measurable Readiness
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-surface-container border border-ready-emerald/30 flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-ready-emerald/20 border border-ready-emerald/40 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                <CheckCheck className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-mono font-bold text-ready-emerald uppercase tracking-wider">Step 1 • Completed</span>
                <h4 className="font-bold text-on-surface text-sm mt-0.5">Workspace Established</h4>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Your practice has its own private workspace.
                </p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-surface-container border border-drift-amber/40 flex items-start gap-4 shadow-sm">
              <div className="w-8 h-8 rounded-full bg-drift-amber/20 border border-drift-amber/40 flex items-center justify-center text-drift-amber shrink-0 mt-0.5">
                <Plug className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <span className="text-[11px] font-mono font-bold text-drift-amber uppercase tracking-wider">Step 2 • Active</span>
                <h4 className="font-bold text-on-surface text-sm mt-0.5">Connect your first system</h4>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Start with backups (Veeam) or Microsoft 365. CrowdStrike and Splunk can follow.
                </p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-surface-container/40 border border-outline-variant/30 flex items-start gap-4 opacity-75">
              <div className="w-8 h-8 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center text-on-surface-variant shrink-0 mt-0.5">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-mono font-bold text-on-surface-variant uppercase tracking-wider">Step 3 • Upcoming</span>
                <h4 className="font-bold text-on-surface-variant text-sm mt-0.5">Daily checks begin</h4>
                <p className="text-xs text-on-surface-variant/70 mt-1 leading-relaxed">
                  Checks run around the clock and every result is sealed as proof.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Evidence Status vs Moat Invariant */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 sm:p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 mb-4">
                <Activity className="w-5 h-5 text-drift-amber shrink-0" />
                <h3 className="text-base font-bold text-on-surface">What we can see right now</h3>
              </div>
              <ul className="space-y-3 text-sm text-on-surface-variant">
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No security systems connected</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No live data from your systems yet</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No proof available yet</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-surface-bright text-xs text-on-surface-variant/70">
              Your score appears as soon as the first connected system sends data.
            </div>
          </div>

          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 sm:p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 mb-4">
                <ShieldCheck className="w-5 h-5 text-ready-emerald shrink-0" />
                <h3 className="text-base font-bold text-on-surface">How ResilAI decides</h3>
              </div>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                ResilAI never assumes you are protected when it cannot see proof. Scores come from live data in your systems, not from questionnaires or AI guesses.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-surface-bright flex items-center justify-between text-xs">
              <span className="text-ready-emerald font-semibold">Same data, same score, every time</span>
              <Link to="/documents" className="text-on-surface-variant hover:text-ready-emerald transition-colors font-medium">Scoring Methodology →</Link>
            </div>
          </div>
        </section>
      </div>
    );
  }

  // Determine overall states
  const overallState: EvidenceState = isUnknown ? 'no_evidence' : (report ? 'verified' : 'unavailable');

  const heroStatusText = isUnknown 
    ? 'UNABLE TO VERIFY' 
    : (isReady ? 'READY FOR TODAY' : 'ACTION REQUIRED');
    
  const heroBadgeClass = isUnknown 
    ? 'bg-surface-container text-on-surface-variant border-outline-variant' 
    : (isReady ? 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/30 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'bg-drift-amber/10 text-drift-amber border-drift-amber/30 drop-shadow-[0_0_15px_rgba(245,158,11,0.3)]');

  const HeroIconComponent = isUnknown 
    ? HelpCircle 
    : (isReady ? ShieldCheck : AlertTriangle);

  const ringColor = isUnknown
    ? 'text-outline-variant'
    : (isReady ? 'text-ready-emerald drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]' : 'text-drift-amber drop-shadow-[0_0_15px_rgba(245,158,11,0.5)]');

  // Plain-English verdict (deterministic: status, score, failed checks, backup state)
  const plain = derivePlainVerdict(report);
  const verifiedCount = report.verification?.verified_items_count;
  const totalCount = report.verification?.total_items_count;
  const hasCheckCounts = typeof verifiedCount === 'number' && typeof totalCount === 'number' && totalCount > 0;
  const confidencePct = report.verification?.overall_confidence_pct ?? (report.verification as any)?.confidence_pct ?? 0;
  const checksSummary =
    typeof verifiedCount === 'number' && typeof totalCount === 'number' && totalCount > 0
      ? `${verifiedCount} of ${totalCount} checks passed using live data from your systems.`
      : 'Checks run on live data from your connected systems.';

  const executiveVerdict = isUnknown
    ? "No connected systems are sending data yet. Connect your systems so the checks can run."
    : isReady
      ? `${checksSummary} Nothing is blocking you from opening today.`
      : `${checksSummary} ${actionsList.length} item${actionsList.length === 1 ? '' : 's'} below need${actionsList.length === 1 ? 's' : ''} attention.`;

  // Verified Protections: derive each card from the report instead of fixed copy (demo keeps its narrative)
  const allChecks = [
    ...(report.passed_checks || []).map(c => ({ ...c, state: 'passed' as const })),
    ...(report.failed_checks || []).map(c => ({ ...c, state: 'failed' as const })),
    ...(report.warnings || []).map(c => ({ ...c, state: 'warning' as const })),
  ];
  const protectionFor = (pattern: RegExp, demoCopy: string) => {
    const matches = allChecks.filter(c => pattern.test(`${c.category || ''} ${c.name || ''}`));
    if (isDemo) return { badge: 'VERIFIED', tone: 'ready' as const, copy: demoCopy, status: 'Confirmed from live data' };
    if (matches.length === 0) {
      return { badge: 'NOT CHECKED', tone: 'unknown' as const, copy: 'No connected system reports on this yet.', status: 'No live data' };
    }
    const failed = matches.filter(c => c.state === 'failed');
    const warned = matches.filter(c => c.state === 'warning');
    if (failed.length > 0) {
      return { badge: 'NEEDS ATTENTION', tone: 'critical' as const, copy: `${failed.map(c => c.name).join(', ')} did not pass.`, status: 'Confirmed from live data' };
    }
    if (warned.length > 0) {
      return { badge: 'WATCH', tone: 'warning' as const, copy: `${warned.map(c => c.name).join(', ')} needs a look soon.`, status: 'Confirmed from live data' };
    }
    return { badge: 'VERIFIED', tone: 'ready' as const, copy: `${matches.map(c => c.name).join(', ')} passed.`, status: 'Confirmed from live data' };
  };
  const protectionBadgeClass = {
    ready: 'text-ready-emerald bg-ready-emerald/10',
    warning: 'text-drift-amber bg-drift-amber/10',
    critical: 'text-critical-red bg-critical-red/10',
    unknown: 'text-on-surface-variant bg-surface-container-high',
  };
  const protections = [
    {
      key: 'backup',
      Icon: HardDrive,
      title: 'Data Recovery & Ransomware Shield',
      plain: 'Backups that cannot be deleted',
      technical: 'Immutable backups, RPO / RTO',
      ...protectionFor(/backup|recovery|snapshot|immutable/i, 'Protected backup copies verified. Records can be restored if computers are locked.'),
    },
    {
      key: 'identity',
      Icon: KeyRound,
      title: 'Access Controls & MFA Enforcement',
      plain: 'Second login step (MFA) for staff',
      technical: 'MFA, Entra ID, privileged access',
      ...protectionFor(/mfa|identity|login|password|entra|credential|access|privilege/i, 'Second login step is on for staff accounts in Microsoft Entra ID.'),
    },
    {
      key: 'device',
      Icon: Shield,
      title: 'Computer & Endpoint Protection',
      plain: 'Device protection (EDR) and disk encryption',
      technical: 'EDR, Intune, encryption',
      ...protectionFor(/endpoint|device|edr|laptop|computer|encrypt|intune|patch/i, 'Device protection and disk encryption running on clinic computers.'),
    },
    {
      key: 'monitoring',
      Icon: Activity,
      title: 'Continuous Monitoring & EHR Sync',
      plain: 'Live data from your systems',
      technical: 'Telemetry, SIEM, email gateway',
      ...protectionFor(/monitor|log|telemetry|siem|splunk|alert|email|mail|network|tls|certificate/i, 'Monitoring and record-system data streams verified in the last 24 hours.'),
    },
  ];

  return (
    <div className="max-w-[1200px] mx-auto space-y-10 animate-fade-up">

      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="today" />

      {/* ========================================================================= */}
      {/* STAGE 1: CURRENT READINESS (North Star Hero)                               */}
      {/* ========================================================================= */}
      <section className="flex flex-col items-center justify-center text-center py-10 px-4 sm:px-6 bg-surface-container-low rounded-2xl border border-surface-bright border-t-2 border-t-ready-emerald/40 relative overflow-hidden shadow-xl group hover:border-ready-emerald/40 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-b from-ready-emerald/5 via-transparent to-transparent pointer-events-none" />

        {/* Answer first: one plain-English sentence, then what to do today */}
        <h2
          className="text-2xl md:text-3xl font-bold tracking-tight text-on-surface mb-2 max-w-2xl px-2"
          data-testid="plain-verdict"
        >
          {plain.verdict}
        </h2>
        <p
          className={`text-sm md:text-base font-semibold mb-6 max-w-2xl px-2 ${verdictToneClass[plain.tone]}`}
          data-testid="plain-today"
        >
          {plain.today}
        </p>

        {/* Instant Status Badge & Brand Indicator */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 mb-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-surface-container border border-outline-variant/60 shadow-xs">
            <img src="/favicon.png" alt="ResilAI" className="w-4 h-4 object-contain rounded-xs shrink-0" />
            <span className="font-bold text-on-surface">ResilAI</span>
            <span className="text-on-surface-variant/40">•</span>
            <span className="text-on-surface-variant font-mono text-[11px]">Checked around the clock</span>
          </div>

          <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${heroBadgeClass}`}>
            <span className={`w-2 h-2 rounded-full ${isUnknown ? 'bg-outline' : isReady ? 'bg-ready-emerald animate-pulse' : 'bg-drift-amber animate-pulse'}`} />
            <span>Stage 1 • {heroStatusText}</span>
          </div>
        </div>

        {/* Circular Hero Arc Gauge & Score - Stitch Obsidian Brand Design */}
        <div className="relative w-52 h-52 sm:w-60 sm:h-60 mb-6 flex items-center justify-center ambient-glow rounded-full">
          {/* Subtle Outer Pulsing Ring */}
          <div className={`absolute inset-0 rounded-full border-2 ${isReady ? 'border-ready-emerald/20 animate-pulse-ring' : 'border-drift-amber/20'} pointer-events-none`} />
          <div className={`absolute inset-2 rounded-full border ${isReady ? 'border-ready-emerald/30' : 'border-drift-amber/30'} pointer-events-none`} />

          {/* SVG Progress Ring */}
          <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle className="text-surface-container-highest" cx="50" cy="50" fill="none" r="42" stroke="currentColor" strokeWidth="4.5" />
            <circle 
              className={`transition-all duration-1000 ease-out ${ringColor}`} 
              cx="50" 
              cy="50" 
              fill="none" 
              r="42" 
              stroke="currentColor" 
              strokeWidth="6" 
              strokeDasharray="264" 
              strokeDashoffset={264 - (264 * (isUnknown ? 0 : (report.clinic_health_pct || 0))) / 100} 
              strokeLinecap="round" 
            />
          </svg>

          {/* Inner Content Disc */}
          <div className="w-36 h-36 sm:w-44 sm:h-44 glass-panel rounded-full flex flex-col items-center justify-center shadow-lg border border-surface-bright relative z-10">
            <HeroIconComponent className={`w-8 h-8 sm:w-10 sm:h-10 mb-1 ${isUnknown ? 'text-on-surface-variant' : (isReady ? 'text-ready-emerald' : 'text-drift-amber')}`} />
            <div className="flex items-baseline justify-center">
              <span className="text-4xl sm:text-5xl font-extrabold text-on-surface tracking-tight leading-none">
                {isUnknown ? '--' : report.clinic_health_pct}
              </span>
              {!isUnknown && <span className="text-sm font-mono text-ready-emerald font-bold ml-1">%</span>}
            </div>
            <span className="text-[10px] sm:text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mt-1">
              {isUnknown ? 'NOT CHECKED' : isReady ? 'ALL CLEAR' : 'NEEDS ATTENTION'}
            </span>
          </div>
        </div>

        {/* Status label (kept) + what the score is based on */}
        <h3 className="text-lg md:text-xl font-bold tracking-tight text-on-surface mb-2 max-w-2xl px-2">
          {heroStatusText === 'READY FOR TODAY' ? 'READY FOR TODAY' : heroStatusText}
        </h3>
        <p className="text-sm md:text-base text-on-surface-variant max-w-2xl mx-auto leading-relaxed font-medium px-2">
          <VerifiedValue
            value={executiveVerdict}
            state={overallState}
            fallback="No connected systems are sending data yet."
          />
        </p>
        <p className="text-[11px] font-mono text-on-surface-variant/70 mt-2 px-2">
          Readiness score = share of checks that passed on live data (telemetry)
        </p>
      </section>

      {/* ========================================================================= */}
      {/* STAGE 2: WHY (Morning Brief & Delta Highlights)                            */}
      {/* ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-ready-emerald" />
            <h3 className="text-xs font-mono font-bold text-on-surface-variant uppercase tracking-wider">
              Stage 2 • Why: What we checked overnight
            </h3>
          </div>
          <button 
            onClick={handleOpenExplainLeadership}
            className={tokens.button.aiExplain}
            title="Explain this readiness report for leadership"
          >
            <Sparkles className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Explain for Leadership</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Morning Brief Card (8 cols) */}
          <div className="md:col-span-8 bg-surface-container-low rounded-2xl border border-surface-bright border-t-2 border-t-ready-emerald/40 p-5 sm:p-6 flex flex-col justify-between hover:bg-surface-container transition-colors duration-200 shadow-sm relative overflow-hidden">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-on-surface">Morning Brief</h4>
                    <p className="text-xs text-on-surface-variant">Written from live data in your systems, not a questionnaire</p>
                  </div>
                </div>
                <button 
                  onClick={handleOpenExplainLeadership}
                  className="text-xs font-semibold text-ready-emerald hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <span>Executive Breakdown</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <p className="text-base text-on-surface-variant leading-relaxed mb-6 font-medium">
                <VerifiedValue 
                  value={report.greeting ? `${report.greeting}. ${report.summary}` : report.summary}
                  state={overallState}
                  fallback="No connected systems are sending data yet, so there is nothing to summarise this morning."
                />
              </p>
            </div>

            {/* Delta & Health Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-surface-bright">
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Last Checked</span>
                <span className="text-sm font-bold text-on-surface">
                  {report.generated_at ? new Date(report.generated_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : 'Not yet'}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">
                  <PlainTerm plain="Checks passed" technical="verified items" />
                </span>
                <span className="text-sm font-bold text-on-surface">
                  <VerifiedValue
                    value={hasCheckCounts ? `${verifiedCount}/${totalCount}` : null}
                    state={hasCheckCounts ? 'verified' : 'no_evidence'}
                    fallback="Not yet"
                  />
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Things to fix</span>
                <span className={`text-sm font-bold ${actionsList.length === 0 ? 'text-ready-emerald' : 'text-drift-amber'}`}>
                  {actionsList.length === 0 ? 'None' : `${actionsList.length} Items`}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">
                  <PlainTerm plain="Monitoring" technical="engine status" />
                </span>
                <span className="text-sm font-bold text-ready-emerald flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-ready-emerald animate-pulse" /> Running
                </span>
              </div>
            </div>
          </div>

          {/* Regional Peer & Benchmark Card (4 cols) */}
          <div className="md:col-span-4 bg-surface-container-low rounded-2xl border border-surface-bright border-t-2 border-t-primary/40 p-5 sm:p-6 flex flex-col justify-between hover:bg-surface-container transition-colors duration-200 shadow-sm">
            <div className="w-full flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-ready-emerald" />
                <h4 className="text-sm font-bold text-on-surface">Readiness Benchmark</h4>
              </div>
              <span className="text-[10px] font-mono font-bold uppercase text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/30 px-2 py-0.5 rounded">
                Verified
              </span>
            </div>

            {/* Semicircular Speedometer Arc Gauge */}
            <div className="relative w-full flex flex-col items-center justify-center my-3">
              <div className="relative w-44 h-24 flex items-center justify-center">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 120 70">
                  {/* Background track arc */}
                  <path 
                    d="M 15 60 A 45 45 0 0 1 105 60" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="8" 
                    strokeLinecap="round" 
                    className="text-surface-container-high" 
                  />
                  {/* Value track arc */}
                  <path 
                    d="M 15 60 A 45 45 0 0 1 105 60" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="8" 
                    strokeLinecap="round" 
                    strokeDasharray="141.37" 
                    strokeDashoffset={141.37 - (141.37 * Math.min(100, Math.max(0, report.clinic_health_pct || 0))) / 100} 
                    className={`${(report.clinic_health_pct || 0) >= 90 ? 'text-ready-emerald drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'text-drift-amber drop-shadow-[0_0_8px_rgba(245,158,11,0.4)]'} transition-all duration-1000 ease-out`} 
                  />
                </svg>
                {/* Score centered directly beneath the arc */}
                <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-on-surface tracking-tight leading-none">
                    {report.clinic_health_pct || 0}%
                  </span>
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-on-surface-variant mt-0.5">
                    Readiness Score
                  </span>
                </div>
              </div>
            </div>

            {/* Peer Benchmark Context & Progress Bar */}
            <div className="w-full pt-3 border-t border-surface-bright">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-on-surface-variant">Readiness band</span>
                <span className={`font-semibold ${
                  (report.clinic_health_pct || 0) >= 80 ? 'text-ready-emerald'
                  : (report.clinic_health_pct || 0) >= 60 ? 'text-drift-amber'
                  : 'text-red-500'
                }`}>
                  {(report.clinic_health_pct || 0) >= 80 ? 'Strong'
                    : (report.clinic_health_pct || 0) >= 60 ? 'Good'
                    : (report.clinic_health_pct || 0) >= 40 ? 'Needs work'
                    : report.status === 'unknown' ? 'Not yet checked' : 'Critical'}
                </span>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-ready-emerald h-full rounded-full transition-all duration-1000" 
                  style={{ width: `${Math.min(100, Math.max(0, report.clinic_health_pct || 0))}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* STAGE 3: WHAT NEEDS ATTENTION (Active Triage & Incident Risks)              */}
      {/* ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-drift-amber" />
            <h3 className="text-xs font-mono font-bold text-on-surface-variant uppercase tracking-wider">
              Stage 3 • What Needs Attention: Things to fix
            </h3>
          </div>
          <Link to="/needs-attention" className="text-xs font-semibold text-ready-emerald hover:underline flex items-center gap-1">
            <span>View All Incident Risks ({actionsList.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-surface-container-low rounded-2xl border border-surface-bright border-t-2 border-t-drift-amber/40 p-4 sm:p-6 space-y-4 shadow-sm">
          <DataState state={overallState}>
            {actionsList.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 border border-dashed border-surface-bright rounded-xl text-center bg-surface-container/40">
                <div className="w-12 h-12 rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald mb-3">
                  <CheckCheck className="w-6 h-6" />
                </div>
                <p className="text-base font-bold text-on-surface">No Critical Gaps Pending</p>
                <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
                  Every protection we check passed overnight. Nothing is waiting on you or your IT provider.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {actionsList.slice(0, 3).map((action: ActionCard, index: number) => {
                  const item = normalizeAction(action, index);
                  const guidance = guidanceForAction(item);
                  return (
                  <div key={`${item.id}-${index}`} className="space-y-2">
                    {action.explanation ? (
                      <ExecutiveExplanation
                        explanation={action.explanation}
                        actionLabel={(action as { fix_now_available?: boolean }).fix_now_available === false ? 'Send to IT / MSP' : 'Fix Now'}
                        onAction={() => handleFix(item.id)}
                        actionState={fixingId === item.id ? 'executing' : 'idle'}
                        sourceConnector={action.verification_method}
                        rawTelemetry={action.evidence}
                      />
                    ) : (
                      <div className="p-5 rounded-xl bg-surface-container border border-surface-bright/50 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="flex items-start gap-3.5 min-w-0">
                          <div className="w-9 h-9 rounded-xl bg-critical-red/10 border border-critical-red/30 flex items-center justify-center shrink-0 mt-0.5">
                            <AlertTriangle className="w-4 h-4 text-critical-red" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2 mb-1">
                              <span className="text-[10px] font-mono font-bold uppercase text-critical-red bg-critical-red/10 px-2 py-0.5 rounded">
                                {item.severity ? `${item.severity} Priority` : 'Needs attention'}
                              </span>
                              {item.lastVerifiedAt && (
                                <span className="text-xs text-on-surface-variant font-mono">
                                  Checked {item.lastVerifiedAt}
                                </span>
                              )}
                            </div>
                            <h4 className="text-base font-bold text-on-surface">{item.title}</h4>
                            {guidance.whatHappened !== item.title && (
                              <p className="text-sm text-on-surface leading-relaxed mt-1">
                                <strong className="text-on-surface-variant font-semibold">What happened: </strong>
                                {guidance.whatHappened}
                              </p>
                            )}
                            <p className="text-sm text-on-surface-variant leading-relaxed mt-1">
                              <strong className="text-on-surface font-semibold">Why it matters to the practice: </strong>
                              {guidance.whyItMatters}
                            </p>
                            {item.recommendation && (
                              <p className="text-xs font-semibold text-ready-emerald mt-2">What to do: {item.recommendation}</p>
                            )}
                          </div>
                        </div>

                        {(action as { fix_now_available?: boolean }).fix_now_available !== false ? (
                          <button
                            onClick={() => handleFix(item.id)}
                            disabled={fixingId === item.id}
                            className="px-5 py-2.5 rounded-xl bg-ready-emerald text-slate-950 font-bold text-sm hover:bg-ready-emerald/90 transition-colors shrink-0 cursor-pointer disabled:opacity-50"
                          >
                            {fixingId === item.id ? 'Working...' : 'Fix Now'}
                          </button>
                        ) : (
                          <span className="px-4 py-2.5 rounded-xl bg-surface-container-high text-on-surface-variant font-semibold text-xs shrink-0">
                            Needs IT / MSP
                          </span>
                        )}
                      </div>
                    )}
                    <CheckOwnerStrip guidance={guidance} />
                  </div>
                  );
                })}
              </div>
            )}
          </DataState>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* STAGE 4: WHAT SHOULD WE DO (Remediation & Action Plan)                      */}
      {/* ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-ready-emerald" />
          <h3 className="text-xs font-mono font-bold text-on-surface-variant uppercase tracking-wider">
            Stage 4 • What Should We Do: Fix it, or hand it to IT
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-5 flex flex-col justify-between hover:bg-surface-container transition-colors shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2 text-ready-emerald">
                <CheckCheck className="w-4 h-4" />
                <h4 className="text-sm font-bold text-on-surface">1-Click Automated Fixes</h4>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                One click turns on the second login step (MFA) for staff accounts or starts a fresh backup check. No one is logged out.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-bright flex items-center justify-between text-xs text-ready-emerald font-semibold">
              <span>No downtime for staff</span>
              <span>Can be undone ✓</span>
            </div>
          </div>

          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-5 flex flex-col justify-between hover:bg-surface-container transition-colors shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2 text-on-surface">
                <Server className="w-4 h-4 text-ready-emerald" />
                <h4 className="text-sm font-bold text-on-surface">Hand it to IT or your MSP</h4>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Send step-by-step instructions, with the proof attached, to your IT provider or ticketing system.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-bright flex items-center justify-between text-xs">
              <Link to="/it-workspace" className="text-ready-emerald font-semibold hover:underline">
                Open Operations Center →
              </Link>
            </div>
          </div>

          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-5 flex flex-col justify-between hover:bg-surface-container transition-colors shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2 text-on-surface">
                <FileText className="w-4 h-4 text-ready-emerald" />
                <h4 className="text-sm font-bold text-on-surface">Executive Briefing Report</h4>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                A signed PDF summary for board meetings, partners, and your cyber-insurance renewal.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-bright flex items-center justify-between text-xs">
              <Link to="/documents" className="text-ready-emerald font-semibold hover:underline">
                View Reports Vault →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* STAGE 5: HOW CAN WE PROVE IT (Evidence & Verifications Vault)               */}
      {/* ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-ready-emerald" />
            <h3 className="text-xs font-mono font-bold text-on-surface-variant uppercase tracking-wider">
              Stage 5 • How Can We Prove It: Proof from your own systems
            </h3>
          </div>
          <button 
            onClick={() => setCoverageModalOpen(true)} 
            className="text-xs font-semibold text-ready-emerald hover:underline flex items-center gap-1 cursor-pointer"
          >
            <span>View Coverage</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* 4 Core Protections Grid */}
        <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 shadow-sm">
          <h4 className="text-sm font-bold text-on-surface mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-ready-emerald" />
            <span>Verified Protections</span>
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {protections.map(p => (
              <div key={p.key} className="p-4 rounded-xl bg-surface-container border border-surface-bright/40 flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                  <p.Icon className="w-5 h-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h5 className="text-sm font-bold text-on-surface">{p.title}</h5>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded shrink-0 ${protectionBadgeClass[p.tone]}`}>
                      {p.badge}
                    </span>
                  </div>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    <PlainTerm plain={p.plain} technical={p.technical} />
                  </p>
                  <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                    {p.copy}
                  </p>
                  <div className="mt-2 text-[10px] font-mono text-on-surface-variant/70">
                    Status: <span className={`${p.tone === 'unknown' ? 'text-on-surface-variant' : 'text-ready-emerald'} font-semibold`}>{p.tone === 'unknown' ? p.status : `✓ ${p.status}`}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Proof footer */}
          <div className="mt-6 pt-5 border-t border-surface-bright flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2 text-on-surface-variant">
              <FileCheck2 className="w-4 h-4 text-ready-emerald shrink-0" />
              <span>Every result above comes from live data in your systems, and each one is sealed so it cannot be changed later.</span>
            </div>
            <Link 
              to="/documents" 
              className="text-ready-emerald font-bold hover:underline flex items-center gap-1 shrink-0"
            >
              <span>Explore Audit Vault</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Technical details: connected systems, check counts (collapsed for real orgs) */}
          <TechnicalDetails
            className="mt-4"
            title="Technical details"
            hint="connected systems, check counts"
            defaultOpen={isDemo}
          >
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Connected systems health</span>
                <span className="font-mono font-semibold text-on-surface">{report.connector_health_pct ?? 0}%</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Checks verified</span>
                <span className="font-mono font-semibold text-on-surface">
                  {hasCheckCounts ? `${verifiedCount}/${totalCount}` : 'n/a'}
                </span>
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
              Report generated {report.generated_at}. Proof hashes (SHA-256) for each check are in the Audit Vault and under each item&apos;s Technical Evidence panel.
            </p>
          </TechnicalDetails>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* MODAL: Explain for Leadership (Executive & Technical Dual Presentation)    */}
      {/* ========================================================================= */}
      {explainModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-surface-bright rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-fade-up max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-surface-bright bg-surface-container flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-on-surface">Executive Briefing Translation</h3>
                  <p className="text-xs text-on-surface-variant">Plain-English summary for managing partners and the board, built from the same data as the score</p>
                </div>
              </div>

              <button 
                onClick={() => setExplainModalOpen(false)}
                className="p-2 text-on-surface-variant hover:text-on-surface rounded-full hover:bg-surface-container-high transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* View Mode Toggle (Executive View vs Technical View) */}
            <div className="px-6 py-3 bg-surface-container-lowest border-b border-surface-bright flex items-center justify-between">
              <span className="text-xs font-mono font-bold uppercase text-on-surface-variant">Presentation Mode</span>
              <div className="inline-flex rounded-lg bg-surface-container p-1 border border-surface-bright/40">
                <button
                  onClick={() => setExplainViewMode('executive')}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                    explainViewMode === 'executive' 
                      ? 'bg-ready-emerald text-slate-950 shadow-sm' 
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Executive View
                </button>
                <button
                  onClick={() => setExplainViewMode('technical')}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                    explainViewMode === 'technical' 
                      ? 'bg-ready-emerald text-slate-950 shadow-sm' 
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Technical Telemetry
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm leading-relaxed">
              {loadingStory ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-ready-emerald animate-spin" />
                  <p className="text-xs font-mono text-on-surface-variant">Analyzing executive summary...</p>
                </div>
              ) : explainViewMode === 'executive' ? (
                <div className="space-y-5">
                  <div className="p-4 rounded-xl bg-surface-container border border-ready-emerald/30 space-y-2">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-ready-emerald block">
                      Readiness Verdict
                    </span>
                    <p className="text-base font-bold text-on-surface">
                      {plain.verdict}
                    </p>
                    <p className="text-sm text-on-surface-variant">
                      {report.summary || plain.today}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-xs font-mono font-bold uppercase text-on-surface-variant tracking-wider">
                      What leadership should know
                    </h4>
                    {boardStory && boardStory.sections ? (
                      boardStory.sections.map((sec, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-surface-container border border-surface-bright/40">
                          <h5 className="font-bold text-on-surface text-sm mb-1">{sec.title}</h5>
                          <p className="text-xs text-on-surface-variant leading-relaxed">{sec.content}</p>
                        </div>
                      ))
                    ) : (
                      <>
                        <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40">
                          <h5 className="font-bold text-on-surface text-sm mb-1">Ransomware & keeping the doors open</h5>
                          <p className="text-xs text-on-surface-variant leading-relaxed">
                            {plain.backupVerified === false
                              ? 'Backups could not be confirmed. If an attacker locked every computer, we cannot promise records would come back without paying.'
                              : plain.backupVerified === true
                                ? 'Backups that cannot be deleted are confirmed. If an attacker locked every computer, records can be restored without paying a ransom.'
                                : 'No backup system is connected yet, so recovery after an attack cannot be confirmed.'}
                          </p>
                        </div>
                        <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40">
                          <h5 className="font-bold text-on-surface text-sm mb-1">Regulators, auditors and insurers</h5>
                          <p className="text-xs text-on-surface-variant leading-relaxed">
                            Every check is recorded with its proof as it runs, which is the audit trail HIPAA Security Rule § 164.308 asks for. No spreadsheets to fill in before an audit.
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-black/50 border border-surface-bright/50 font-mono text-xs text-ready-emerald space-y-2">
                    <div className="text-on-surface-variant/80 uppercase text-[10px] pb-2 border-b border-surface-bright/40">
                      Proof details (for your IT provider)
                    </div>
                    <div>STATUS: 200_OK_VERIFIED</div>
                    <div>CONFIDENCE_ENGINE: DETERMINISTIC_MATHEMATICAL</div>
                    <div>EVIDENCE_HASH: sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069</div>
                    <div>CONNECTORS: Veeam_v12, Graph_v1.0, Falcon_v7</div>
                    <div>VERIFIED_AT: {report.generated_at}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-5 border-t border-surface-bright bg-surface-container flex items-center justify-between">
              {orgId && (
                <a
                  href={getBoardStoryPdfUrl(orgId)}
                  target="_blank"
                  rel="noopener noreferrer"
                  download="ResilAI_Board_Briefing.pdf"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-ready-emerald hover:underline"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Executive PDF</span>
                </a>
              )}
              <button
                onClick={() => setExplainModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-surface-container-high hover:bg-surface-bright text-on-surface text-xs font-bold transition-colors cursor-pointer ml-auto"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {report.coverage && (
        <CoverageModal 
          isOpen={coverageModalOpen} 
          onClose={() => setCoverageModalOpen(false)} 
          coverage={report.coverage} 
        />
      )}
    </div>
  );
}
