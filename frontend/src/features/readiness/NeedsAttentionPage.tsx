import { useState, useEffect } from 'react';
import { getDailyReadinessReport, triggerProblemFix } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { DataState, EvidenceState } from '../../components/evidence/EvidenceState';
import { ExecutiveExplanation } from '../../components/evidence/ExecutiveExplanation';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileText,
  CheckSquare,
  Wrench,
  RotateCcw,
  Building,
  ArrowRight,
} from 'lucide-react';

export default function NeedsAttentionPage() {
  const { orgId, hasOrg, isDemo, loading: orgLoading } = useActiveOrg();
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [remediationStates, setRemediationStates] = useState<Record<string, 'idle' | 'executing' | 'verifying' | 'verified' | 'unable_to_verify'>>({});

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
      setError(err.message || "Failed to load triage items");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orgId) {
      loadReport();
    } else {
      setLoading(false);
    }
  }, [orgId]);

  const handleFix = async (problemId: string) => {
    setRemediationStates(prev => ({ ...prev, [problemId]: 'executing' }));
    
    try {
      await triggerProblemFix(problemId);
      
      setRemediationStates(prev => ({ ...prev, [problemId]: 'verifying' }));
      
      setTimeout(async () => {
        try {
          const freshData = await getDailyReadinessReport(orgId);
          setReport(freshData);
          
          const stillFailing = freshData.immediate_actions?.some((a: any) => (a.id || a.action_id) === problemId);
          if (stillFailing) {
            setRemediationStates(prev => ({ ...prev, [problemId]: 'unable_to_verify' }));
          } else {
            setRemediationStates(prev => ({ ...prev, [problemId]: 'verified' }));
          }
        } catch {
          setRemediationStates(prev => ({ ...prev, [problemId]: 'unable_to_verify' }));
        }
      }, 3000);

    } catch (err) {
      console.error('Fix execution failed:', err);
      setRemediationStates(prev => ({ ...prev, [problemId]: 'unable_to_verify' }));
    }
  };

  if (orgLoading || loading) return <LoadingState />;

  if (!hasOrg && !isDemo) {
    return (
      <div className="space-y-8 animate-fade-up max-w-2xl mx-auto py-12">
        <div className="bg-slate-900/60 dark:bg-slate-900/60 rounded-3xl border border-slate-800 p-8 sm:p-10 text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Building className="w-8 h-8 text-emerald-500" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
              Set up your readiness workspace
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
              Create an organization to establish continuous evidence collection and triage readiness issues.
            </p>
          </div>
          <div>
            <Link
              to="/onboarding?new=true"
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-br from-primary-600 to-emerald-500 text-white text-sm font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 transition-all active:scale-[0.98]"
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

  const isUnknown = report.status === 'unknown' || (report.verification && report.verification.overall_confidence_pct === 0);
  const overallState: EvidenceState = isUnknown ? 'no_evidence' : (report ? 'verified' : 'unavailable');

  const actions = report.immediate_actions || [];
  const failedChecks = report.failed_checks || [];
  const warnings = report.warnings || [];

  return (
    <div className="space-y-8 animate-fade-up max-w-5xl">
      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="needs-attention" />

      {/* Top Banner */}
      <section className="bg-surface-container-low p-6 rounded-2xl border border-surface-bright flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-on-surface">Triage & Immediate Action</h1>
          <p className="text-sm text-on-surface-variant mt-1">
            Resolve control gaps detected during deterministic readiness verification.
          </p>
        </div>
        <button
          onClick={loadReport}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-surface-container text-xs font-semibold text-on-surface hover:bg-surface-container-high border border-outline-variant/40 transition-all shrink-0"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Re-evaluate Gaps</span>
        </button>
      </section>

      {/* Critical Blockers / Immediate Actions */}
      <section className="space-y-4">
        <div className="flex items-center gap-3 pb-2 border-b border-outline-variant/30">
          <div className="w-3 h-3 rounded-full bg-critical-red" />
          <h2 className="text-lg font-semibold text-on-surface">Critical Readiness Gaps</h2>
          <span className="ml-auto text-xs font-mono text-critical-red bg-critical-red/10 px-2.5 py-1 rounded-full">
            {actions.length} Requiring Executive Action
          </span>
        </div>

        <DataState state={overallState}>
          {actions.length === 0 && failedChecks.length === 0 ? (
            <div className="p-8 rounded-xl bg-surface-container-low border border-surface-bright flex flex-col items-center justify-center text-center">
              <CheckCircle2 className="w-12 h-12 text-ready-emerald mb-2" />
              <h3 className="text-base font-semibold text-on-surface">Zero Critical Blockers</h3>
              <p className="text-xs text-on-surface-variant max-w-md mt-1">
                Your clinical systems passed overnight verifications. All access controls and encryption baselines are active.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {actions.map((action: any) => {
                const actionId = action.id || action.action_id;
                const rState = remediationStates[actionId] || 'idle';
                
                return (
                  <div key={actionId}>
                    {action.explanation ? (
                      <ExecutiveExplanation
                        explanation={action.explanation}
                        actionLabel="Fix Issue Now"
                        onAction={() => handleFix(actionId)}
                        actionState={rState}
                      />
                    ) : (
                      <article className={`bg-surface-container-low rounded-xl p-6 border ${rState === 'unable_to_verify' ? 'border-drift-amber/50' : 'border-surface-bright hover:border-critical-red/40'} flex flex-col gap-4 relative overflow-hidden group transition-colors`}>
                        <div className={`absolute top-0 left-0 w-1.5 h-full ${rState === 'unable_to_verify' ? 'bg-drift-amber' : 'bg-critical-red'}`} />
                        
                        <div className="flex justify-between items-start">
                          <div className={`flex items-center gap-2 text-xs font-medium ${rState === 'unable_to_verify' ? 'text-drift-amber' : 'text-critical-red'}`}>
                            {rState === 'unable_to_verify' ? (
                              <AlertTriangle className="w-4 h-4" />
                            ) : (
                              <AlertCircle className="w-4 h-4" />
                            )}
                            <span>{rState === 'unable_to_verify' ? 'Verification Failed' : 'Critical Blocker'}</span>
                          </div>
                          <span className="text-xs font-mono text-on-surface-variant">
                            {rState === 'idle' && 'Active'}
                            {rState === 'executing' && 'Remediating...'}
                            {rState === 'verifying' && 'Polling Telemetry...'}
                            {rState === 'unable_to_verify' && 'Manual Action Required'}
                          </span>
                        </div>

                        <div>
                          <h3 className="text-base font-semibold text-on-surface mb-1">{action.problem || action.title}</h3>
                          <p className="text-sm text-on-surface-variant">{action.why_it_matters || action.description}</p>
                        </div>

                        <div className={`flex flex-col gap-2 bg-surface-container p-3 rounded-lg mt-1 border ${rState === 'unable_to_verify' ? 'border-drift-amber/30 bg-drift-amber/5' : 'border-outline-variant/30'}`}>
                          <div className="flex items-start gap-2 text-sm text-on-surface-variant">
                            <FileText className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                            <span><strong className="text-on-surface">What to do:</strong> {action.recommended_action || "Run immediate automated remediation"}</span>
                          </div>
                          <div className="flex items-start gap-2 text-sm text-on-surface-variant pt-2 border-t border-outline-variant/30">
                            <CheckSquare className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                            <span><strong className="text-on-surface">How we know:</strong> {action.technical_evidence || "Verified via deterministic telemetry collection"}</span>
                          </div>
                        </div>

                        {rState === 'unable_to_verify' && (
                          <div className="mt-2 p-3 bg-drift-amber/10 border border-drift-amber/30 rounded-lg flex gap-3 text-sm text-on-surface">
                            <Wrench className="w-4 h-4 text-drift-amber shrink-0 mt-0.5" />
                            <div>
                              <p className="font-semibold text-drift-amber">Unable to verify resolution</p>
                              <p className="text-xs text-on-surface-variant mt-1">
                                The automated fix was dispatched, but backend telemetry has not confirmed the change. Physical/manual verification in the source system is required. Do not assume this is resolved.
                              </p>
                            </div>
                          </div>
                        )}

                        <div className="flex items-center justify-between gap-3 mt-2 pt-4 border-t border-outline-variant/40">
                          <span className="text-xs text-on-surface-variant font-mono">
                            {rState === 'unable_to_verify' ? 'Escalate to IT Operations' : 'Est. Fix: ~5 mins'}
                          </span>
                          <button
                            onClick={() => handleFix(actionId)}
                            disabled={rState === 'executing' || rState === 'verifying'}
                            className={`px-5 py-2 rounded-lg text-xs font-medium transition-all shadow-md ${
                              rState === 'unable_to_verify' 
                                ? 'bg-surface-container-high text-on-surface hover:bg-surface-bright border border-outline-variant/50' 
                                : 'bg-ready-emerald text-on-primary-container hover:brightness-110 shadow-ready-emerald/10'
                            } disabled:opacity-50`}
                          >
                            {rState === 'idle' && 'Fix Issue Now'}
                            {rState === 'executing' && 'Executing Fix...'}
                            {rState === 'verifying' && 'Re-checking Evidence...'}
                            {rState === 'unable_to_verify' && 'Retry Verification'}
                          </button>
                        </div>
                      </article>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </DataState>
      </section>

      {/* Warnings & Compliance Drift Section */}
      {warnings.length > 0 && (
        <section className="space-y-4 pt-4">
          <div className="flex items-center gap-3 pb-2 border-b border-outline-variant/30">
            <div className="w-3 h-3 rounded-full bg-drift-amber" />
            <h2 className="text-lg font-semibold text-on-surface">Warnings & Readiness Drift</h2>
            <span className="ml-auto text-xs font-mono text-drift-amber bg-drift-amber/10 px-2.5 py-1 rounded-full">
              {warnings.length} Monitored
            </span>
          </div>

          <DataState state={overallState}>
            <div className="grid grid-cols-1 gap-6">
              {warnings.map((check: any, idx: number) => (
                <div key={idx}>
                  {check.explanation ? (
                    <ExecutiveExplanation explanation={check.explanation} />
                  ) : (
                    <article className="bg-surface-container-low rounded-xl p-6 border border-surface-bright flex flex-col gap-3 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1.5 h-full bg-drift-amber" />
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-medium text-drift-amber flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4" />
                          <span>Operational Warning</span>
                        </span>
                        <span className="text-xs font-mono text-on-surface-variant">Checked Today</span>
                      </div>
                      <h3 className="text-base font-semibold text-on-surface">{check.label}</h3>
                      <p className="text-sm text-on-surface-variant">{check.detail || "Verification suggests control review is recommended."}</p>
                    </article>
                  )}
                </div>
              ))}
            </div>
          </DataState>
        </section>
      )}
    </div>
  );
}
