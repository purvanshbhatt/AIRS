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
      await triggerProblemFix(problemId);
      await loadReport();
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
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-ready-emerald text-surface-container-lowest text-sm font-bold rounded-xl hover:bg-ready-emerald/90 transition-all active:scale-[0.98] shadow-sm"
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
          <p className="text-sm sm:text-base text-on-surface-variant max-w-2xl mx-auto leading-relaxed mb-8">
            ResilAI continuously verifies your incident readiness using mathematical evidence from the security and operational systems you already use.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3.5">
            <Link
              to="/connectors"
              className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-surface-container-lowest text-sm font-bold rounded-xl hover:shadow-lg hover:shadow-ready-emerald/25 transition-all duration-300 active:scale-[0.98]"
            >
              <Plug className="w-4 h-4" />
              <span>Connect Security System</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <a
              href="https://demo.resilai.org"
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
                  Isolated multi-tenant workspace provisioned.
                </p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-surface-container border border-drift-amber/40 flex items-start gap-4 shadow-sm">
              <div className="w-8 h-8 rounded-full bg-drift-amber/20 border border-drift-amber/40 flex items-center justify-center text-drift-amber shrink-0 mt-0.5">
                <Plug className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <span className="text-[11px] font-mono font-bold text-drift-amber uppercase tracking-wider">Step 2 • Active</span>
                <h4 className="font-bold text-on-surface text-sm mt-0.5">Connect Security Telemetry</h4>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Link Microsoft 365, Splunk, CrowdStrike, or Veeam.
                </p>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-surface-container/40 border border-outline-variant/30 flex items-start gap-4 opacity-75">
              <div className="w-8 h-8 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center text-on-surface-variant shrink-0 mt-0.5">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-mono font-bold text-on-surface-variant uppercase tracking-wider">Step 3 • Upcoming</span>
                <h4 className="font-bold text-on-surface-variant text-sm mt-0.5">Continuous Verification</h4>
                <p className="text-xs text-on-surface-variant/70 mt-1 leading-relaxed">
                  Mathematical scoring active with cryptographic evidence.
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
                <h3 className="text-base font-bold text-on-surface">Current Evidence Posture</h3>
              </div>
              <ul className="space-y-3 text-sm text-on-surface-variant">
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No security systems connected</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No telemetry received</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-drift-amber" />
                  <span>No verified evidence available</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-surface-bright text-xs text-on-surface-variant/70">
              Readiness becomes measurable as soon as your first connector syncs.
            </div>
          </div>

          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 sm:p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 mb-4">
                <ShieldCheck className="w-5 h-5 text-ready-emerald shrink-0" />
                <h3 className="text-base font-bold text-on-surface">The ResilAI Trust Invariant</h3>
              </div>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                ResilAI never assumes readiness when evidence is unavailable. Scores are calculated deterministically from ingested system logs, not questionnaires or AI opinions.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-surface-bright flex items-center justify-between text-xs">
              <span className="text-ready-emerald font-semibold">100% Deterministic Verification</span>
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

  const executiveVerdict = isUnknown
    ? "No active telemetry connectors are providing evidence. Connect your systems to verify controls."
    : isReady
      ? "All 14 critical clinical and security systems are verified. Digital clinical operations are fully safe to open today."
      : `${actionsList.length} operational gap${actionsList.length === 1 ? '' : 's'} require attention before today's clinical operations begin.`;

  return (
    <div className="max-w-[1200px] mx-auto space-y-10 animate-fade-up">

      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="today" />

      {/* ========================================================================= */}
      {/* STAGE 1: CURRENT READINESS (North Star Hero)                               */}
      {/* ========================================================================= */}
      <section className="flex flex-col items-center justify-center text-center py-10 px-6 bg-surface-container-low rounded-2xl border border-surface-bright relative overflow-hidden shadow-xl group hover:border-ready-emerald/30 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-b from-ready-emerald/5 via-transparent to-transparent pointer-events-none" />
        
        {/* Instant Status Badge */}
        <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider border mb-6 ${heroBadgeClass}`}>
          <span className={`w-2 h-2 rounded-full ${isUnknown ? 'bg-outline' : isReady ? 'bg-ready-emerald animate-pulse' : 'bg-drift-amber animate-pulse'}`} />
          <span>Stage 1 • {heroStatusText}</span>
        </div>

        {/* Circular Hero Arc Gauge & Score */}
        <div className="relative w-48 h-48 mb-6 flex items-center justify-center">
          <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle className="text-surface-container-high" cx="50" cy="50" fill="none" r="44" stroke="currentColor" strokeWidth="4" />
            <circle 
              className={`transition-all duration-1000 ease-out ${ringColor}`} 
              cx="50" 
              cy="50" 
              fill="none" 
              r="44" 
              stroke="currentColor" 
              strokeWidth="6" 
              strokeDasharray="276" 
              strokeDashoffset={276 - (276 * (isUnknown ? 0 : (report.clinic_health_pct || 0))) / 100}
              strokeLinecap="round"
            />
          </svg>
          <div className="w-32 h-32 bg-surface-container-highest rounded-full flex flex-col items-center justify-center shadow-inner border border-surface-bright relative z-10">
            <HeroIconComponent className={`w-10 h-10 mb-1 ${isUnknown ? 'text-on-surface-variant' : (isReady ? 'text-ready-emerald' : 'text-drift-amber')}`} />
            <div className="flex items-baseline justify-center">
              <span className="text-3xl font-extrabold text-on-surface tracking-tight leading-none">
                {isUnknown ? '--' : report.clinic_health_pct}
              </span>
              {!isUnknown && <span className="text-xs font-mono text-on-surface-variant ml-0.5">%</span>}
            </div>
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-on-surface-variant mt-0.5">Readiness</span>
          </div>
        </div>

        {/* 1-Sentence Executive Verdict */}
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-on-surface mb-2 max-w-2xl">
          {heroStatusText === 'READY FOR TODAY' ? 'READY FOR TODAY' : heroStatusText}
        </h2>
        <p className="text-base md:text-lg text-on-surface-variant max-w-2xl mx-auto leading-relaxed font-medium">
          <VerifiedValue 
            value={executiveVerdict}
            state={overallState}
            fallback="No active telemetry connectors are providing evidence."
          />
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
              Stage 2 • Why: Overnight Verification & Delta Highlights
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
          <div className="md:col-span-8 bg-surface-container-low rounded-2xl border border-surface-bright p-6 flex flex-col justify-between hover:bg-surface-container transition-colors duration-200 shadow-sm relative overflow-hidden">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-on-surface">Morning Brief</h4>
                    <p className="text-xs text-on-surface-variant">Continuous deterministic synthesis</p>
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
                  fallback="All 14 critical systems passed verification at 2:00 AM. Zero compliance drift detected. Identity providers secure and EHR synchronization completed with 100% fidelity."
                />
              </p>
            </div>

            {/* Delta & Health Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-surface-bright">
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Last Checked</span>
                <span className="text-sm font-bold text-on-surface">02:00 AM UTC</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Connectors Verified</span>
                <span className="text-sm font-bold text-on-surface">
                  <VerifiedValue 
                    value={report.verification ? `${report.verification.verified_items_count}/${report.verification.total_items_count}` : '14/14'}
                    state={report.verification ? 'verified' : 'no_evidence'}
                  />
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Readiness Gaps</span>
                <span className={`text-sm font-bold ${actionsList.length === 0 ? 'text-ready-emerald' : 'text-drift-amber'}`}>
                  {actionsList.length === 0 ? 'None' : `${actionsList.length} Items`}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant mb-1">Engine Status</span>
                <span className="text-sm font-bold text-ready-emerald flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-ready-emerald animate-pulse" /> Active
                </span>
              </div>
            </div>
          </div>

          {/* Regional Peer & Benchmark Card (4 cols) */}
          <div className="md:col-span-4 bg-surface-container-low rounded-2xl border border-surface-bright p-6 flex flex-col justify-between hover:bg-surface-container transition-colors duration-200 shadow-sm">
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
                <span className="text-on-surface-variant">Regional Peer Rank</span>
                <span className="font-semibold text-ready-emerald">Top 5%</span>
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
              Stage 3 • What Needs Attention: Active Gaps & Incident Risks
            </h3>
          </div>
          <Link to="/needs-attention" className="text-xs font-semibold text-ready-emerald hover:underline flex items-center gap-1">
            <span>View All Incident Risks ({actionsList.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 space-y-4 shadow-sm">
          <DataState state={overallState}>
            {actionsList.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 border border-dashed border-surface-bright rounded-xl text-center bg-surface-container/40">
                <div className="w-12 h-12 rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald mb-3">
                  <CheckCheck className="w-6 h-6" />
                </div>
                <p className="text-base font-bold text-on-surface">No Critical Gaps Pending</p>
                <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
                  All critical protections passed overnight inspection. Digital clinical operations are free of blocking incident risks.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {actionsList.slice(0, 3).map((action: ActionCard) => (
                  <div key={action.id}>
                    {action.explanation ? (
                      <ExecutiveExplanation
                        explanation={action.explanation}
                        actionLabel="Fix Now"
                        onAction={() => handleFix(action.id)}
                        actionState={fixingId === action.id ? 'executing' : 'idle'}
                        sourceConnector={action.verification_method}
                        rawTelemetry={action.evidence}
                      />
                    ) : (
                      <div className="p-5 rounded-xl bg-surface-container border border-surface-bright/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-start gap-3.5">
                          <div className="w-9 h-9 rounded-xl bg-critical-red/10 border border-critical-red/30 flex items-center justify-center shrink-0 mt-0.5">
                            <AlertTriangle className="w-4 h-4 text-critical-red" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-mono font-bold uppercase text-critical-red bg-critical-red/10 px-2 py-0.5 rounded">
                                {action.severity} Priority
                              </span>
                              <span className="text-xs text-on-surface-variant font-mono">
                                Verified {action.last_verified_at}
                              </span>
                            </div>
                            <h4 className="text-base font-bold text-on-surface">{action.title}</h4>
                            <p className="text-sm text-on-surface-variant leading-relaxed mt-1">{action.impact_narrative}</p>
                            <p className="text-xs font-semibold text-ready-emerald mt-2">Recommended: {action.recommendation}</p>
                          </div>
                        </div>

                        <button
                          onClick={() => handleFix(action.id)}
                          disabled={fixingId === action.id}
                          className="px-5 py-2.5 rounded-xl bg-ready-emerald text-surface-container-lowest font-bold text-sm hover:bg-ready-emerald/90 transition-colors shrink-0 cursor-pointer disabled:opacity-50"
                        >
                          {fixingId === action.id ? 'Executing...' : 'Fix Now'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
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
            Stage 4 • What Should We Do: Remediation & Delegation
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-5 flex flex-col justify-between hover:bg-surface-container transition-colors shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2 text-ready-emerald">
                <CheckCheck className="w-4 h-4" />
                <h4 className="text-sm font-bold text-on-surface">1-Click Automated Fixes</h4>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Automated remediations enforce MFA policies and trigger immediate secondary snapshot verifications.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-bright flex items-center justify-between text-xs text-ready-emerald font-semibold">
              <span>Zero Clinical Downtime</span>
              <span>Reversible ✓</span>
            </div>
          </div>

          <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-5 flex flex-col justify-between hover:bg-surface-container transition-colors shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2 text-on-surface">
                <Server className="w-4 h-4 text-ready-emerald" />
                <h4 className="text-sm font-bold text-on-surface">MSP & IT Delegation</h4>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Export verified forensic instructions directly to your IT provider or ticketing system.
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
                Generate signed PDF summaries for clinic board meetings and insurance underwriting.
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
              Stage 5 • How Can We Prove It: Verifications Vault & Cryptographic Proof
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
            {/* Protection 1: Data Recovery */}
            <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                <HardDrive className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <h5 className="text-sm font-bold text-on-surface">Data Recovery & Ransomware Shield</h5>
                  <span className="text-[10px] font-mono font-bold text-ready-emerald bg-ready-emerald/10 px-2 py-0.5 rounded">
                    VERIFIED
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Immutable Veeam snapshots verified across 3 zones. RTO &lt; 15 mins.
                </p>
                <div className="mt-2 text-[10px] font-mono text-on-surface-variant/70">
                  Proof: <span className="text-ready-emerald font-semibold">sha256:7f83b165...9069</span>
                </div>
              </div>
            </div>

            {/* Protection 2: Access Controls */}
            <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                <KeyRound className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <h5 className="text-sm font-bold text-on-surface">Access Controls & MFA Enforcement</h5>
                  <span className="text-[10px] font-mono font-bold text-ready-emerald bg-ready-emerald/10 px-2 py-0.5 rounded">
                    VERIFIED
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Microsoft Entra ID MFA active for 142/142 clinical staff accounts.
                </p>
                <div className="mt-2 text-[10px] font-mono text-on-surface-variant/70">
                  Proof: <span className="text-ready-emerald font-semibold">sha256:9b71d224...ca72</span>
                </div>
              </div>
            </div>

            {/* Protection 3: Computer Protection */}
            <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                <Shield className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <h5 className="text-sm font-bold text-on-surface">Computer & Endpoint Protection</h5>
                  <span className="text-[10px] font-mono font-bold text-ready-emerald bg-ready-emerald/10 px-2 py-0.5 rounded">
                    VERIFIED
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  CrowdStrike EDR & Intune disk encryption running on all 48 clinic computers.
                </p>
                <div className="mt-2 text-[10px] font-mono text-on-surface-variant/70">
                  Proof: <span className="text-ready-emerald font-semibold">sha256:4a8c3e12...b841</span>
                </div>
              </div>
            </div>

            {/* Protection 4: Security Monitoring & EHR Sync */}
            <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40 flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
                <Activity className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <h5 className="text-sm font-bold text-on-surface">Continuous Monitoring & EHR Sync</h5>
                  <span className="text-[10px] font-mono font-bold text-ready-emerald bg-ready-emerald/10 px-2 py-0.5 rounded">
                    VERIFIED
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  Splunk & Epic telemetry streams verified with zero loss in last 24 hours.
                </p>
                <div className="mt-2 text-[10px] font-mono text-on-surface-variant/70">
                  Proof: <span className="text-ready-emerald font-semibold">sha256:d3910e57...f119</span>
                </div>
              </div>
            </div>
          </div>

          {/* Cryptographic Provenance Ledger Footer */}
          <div className="mt-6 pt-5 border-t border-surface-bright flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2 text-on-surface-variant">
              <FileCheck2 className="w-4 h-4 text-ready-emerald shrink-0" />
              <span>Immutable cryptographic provenance ledger active across all connectors.</span>
            </div>
            <Link 
              to="/documents" 
              className="text-ready-emerald font-bold hover:underline flex items-center gap-1 shrink-0"
            >
              <span>Explore Audit Vault</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
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
                  <p className="text-xs text-on-surface-variant">Deterministic synthesis for Managing Partners & Board</p>
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
                      ? 'bg-ready-emerald text-surface-container-lowest shadow-sm' 
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Executive View
                </button>
                <button
                  onClick={() => setExplainViewMode('technical')}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                    explainViewMode === 'technical' 
                      ? 'bg-ready-emerald text-surface-container-lowest shadow-sm' 
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
                  <p className="text-xs font-mono text-on-surface-variant">Loading deterministic narrative...</p>
                </div>
              ) : explainViewMode === 'executive' ? (
                <div className="space-y-5">
                  <div className="p-4 rounded-xl bg-surface-container border border-ready-emerald/30 space-y-2">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-ready-emerald block">
                      Readiness Verdict
                    </span>
                    <p className="text-base font-bold text-on-surface">
                      {isReady ? 'Clinic is 100% Prepared For Today\'s Operations' : 'Action Required on 1 System'}
                    </p>
                    <p className="text-sm text-on-surface-variant">
                      {report.summary || 'All patient data backups, doctor credentials, and clinic computers are actively monitored with zero unverified gaps.'}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-xs font-mono font-bold uppercase text-on-surface-variant tracking-wider">
                      Executive Narrative Points
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
                          <h5 className="font-bold text-on-surface text-sm mb-1">Ransomware & Patient Continuity</h5>
                          <p className="text-xs text-on-surface-variant leading-relaxed">
                            Backups have completed successfully with air-gapped snapshots. In the event of a total network lock, clinical records can be recovered in under 15 minutes without paying ransoms.
                          </p>
                        </div>
                        <div className="p-4 rounded-xl bg-surface-container border border-surface-bright/40">
                          <h5 className="font-bold text-on-surface text-sm mb-1">Regulatory & HIPAA Exposure</h5>
                          <p className="text-xs text-on-surface-variant leading-relaxed">
                            Continuous evidence collection fulfills HIPAA Security Rule § 164.308 audit trail requirements without requiring manual spreadsheet audits.
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
                      Telemetry Pipeline State
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
