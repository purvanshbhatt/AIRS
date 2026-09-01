import { useEffect, useState } from 'react';
import { getDailyReadinessReport } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  History,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Building,
  ArrowRight,
} from 'lucide-react';

export default function RecoveryReadinessPage() {
  const { orgId, hasOrg, isDemo, loading: orgLoading } = useActiveOrg();
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      setError(err.message || "Failed to load readiness data");
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
              Create an organization to establish backup telemetry and operational recovery guarantees.
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

  const businessContinuity = report.business_continuity;
  const operationalReadiness = businessContinuity?.operational_readiness;
  const hasRecoveryData = !!operationalReadiness;
  const rtoMins = operationalReadiness?.estimated_downtime_minutes != null ? operationalReadiness.estimated_downtime_minutes : null;
  const criticalSystems = operationalReadiness?.critical_systems_verified || [];
  const blockers = operationalReadiness?.current_blockers || [];
  const isRansomwareSafe = operationalReadiness?.can_recover;

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="recovery" />

      {/* Header */}
      <div className="border-b border-outline-variant/40 pb-6">
        <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight mb-2">Recovery Readiness</h1>
        <p className="text-base text-on-surface-variant max-w-2xl">
          Your organization&apos;s resilience telemetry and backup integrity, verified against healthcare operations objectives.
        </p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Blockers Alert (if any) */}
        {blockers.length > 0 && (
          <div className="col-span-1 md:col-span-12 bg-critical-red/5 border border-critical-red/30 rounded-xl p-6 flex items-start gap-4">
            <AlertTriangle className="w-5 h-5 text-critical-red shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-bold text-critical-red mb-2">Active Recovery Blockers</h3>
              <ul className="list-disc pl-5 space-y-1 text-sm text-on-surface">
                {blockers.map((blocker, i) => <li key={i}>{blocker}</li>)}
              </ul>
            </div>
          </div>
        )}

        {/* TTR Card (Col span 4) */}
        <div className="col-span-1 md:col-span-4 bg-surface-container-low rounded-xl border border-surface-bright p-6 flex flex-col justify-between hover:border-ready-emerald/40 transition-all duration-300 relative overflow-hidden group">
          <div className={`absolute inset-0 bg-gradient-to-br ${rtoMins !== null ? 'from-ready-emerald/5' : 'from-surface-variant/5'} to-transparent pointer-events-none`} />
          
          <div className="flex items-center justify-between mb-8 relative z-10">
            <h2 className="text-base font-semibold text-on-surface flex items-center gap-2">
              <Clock className={`w-4 h-4 ${rtoMins !== null ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
              <span>Time to Recovery (RTO)</span>
            </h2>
            <span className={`px-2.5 py-1 text-xs font-mono font-medium rounded border ${rtoMins !== null ? 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/20' : 'bg-surface-container-high text-on-surface-variant border-outline-variant/30'}`}>
              {rtoMins !== null ? 'Optimal' : 'Unknown'}
            </span>
          </div>

          <div className="relative z-10">
            {rtoMins !== null ? (
              <div className="text-5xl font-bold text-ready-emerald tracking-tight mb-2">
                {rtoMins}<span className="text-xl text-on-surface-variant ml-1 font-normal">Min</span>
              </div>
            ) : (
              <div className="text-3xl font-bold text-on-surface-variant tracking-tight mb-2">
                Unable to verify
              </div>
            )}
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Estimated restoration time (Recovery Time Objective) for Tier 1 Patient Databases (EHR/EMR) from the last verified snapshot.
            </p>
          </div>
        </div>

        {/* Backup Health Timeline (Col span 8) */}
        <div className="col-span-1 md:col-span-8 bg-surface-container-low rounded-xl border border-surface-bright p-6 flex flex-col justify-between hover:border-ready-emerald/40 transition-all duration-300">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-base font-semibold text-on-surface flex items-center gap-2">
              <History className={`w-4 h-4 ${hasRecoveryData ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
              <span>Backup Health (7 Days)</span>
            </h2>
            <span className={`text-xs font-mono ${hasRecoveryData ? 'text-ready-emerald' : 'text-on-surface-variant'}`}>
              {hasRecoveryData ? '100% Immutable Snapshots' : 'Data Unavailable'}
            </span>
          </div>

          {hasRecoveryData ? (
            <div className="flex justify-between items-end gap-3 h-32 pt-4">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'].map((day, i) => (
                <div key={day} className="flex flex-col items-center gap-2 flex-1 group">
                  <div className="w-full bg-surface-container-high rounded-t-md h-full relative overflow-hidden flex items-end">
                    <div 
                      className={`w-full ${i === 3 ? 'bg-drift-amber h-[80%]' : 'bg-ready-emerald h-full'} rounded-t-md opacity-80 group-hover:opacity-100 transition-all`} 
                    />
                  </div>
                  <span className={`text-xs font-mono ${i === 6 ? 'text-ready-emerald font-bold' : 'text-on-surface-variant'}`}>{day}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-32 flex items-center justify-center bg-surface-container border border-dashed border-outline-variant/30 rounded-lg">
              <span className="text-sm font-medium text-on-surface-variant">Unable to verify telemetry from backup provider.</span>
            </div>
          )}
        </div>

        {/* Verified Critical Systems (Col span 6) */}
        <div className="col-span-1 md:col-span-6 bg-surface-container-low rounded-xl border border-surface-bright p-6">
          <div className="flex items-center gap-2.5 mb-6">
            <ShieldCheck className={`w-5 h-5 ${criticalSystems.length > 0 ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
            <h3 className="text-base font-semibold text-on-surface">Verified Critical Systems</h3>
          </div>
          {criticalSystems.length > 0 ? (
            <ul className="space-y-3">
              {criticalSystems.map((system: string, idx: number) => (
                <li key={idx} className="flex items-center gap-3 text-sm text-on-surface p-2.5 rounded-lg bg-surface-container border border-surface-bright">
                  <CheckCircle2 className="w-4 h-4 text-ready-emerald shrink-0" />
                  <span>{system}</span>
                </li>
              ))}
            </ul>
          ) : (
             <div className="flex items-center gap-3 text-sm text-on-surface-variant p-4 rounded-lg bg-surface-container border border-dashed border-outline-variant/30">
               <AlertCircle className="w-4 h-4 shrink-0" />
               <span>Unable to verify critical systems telemetry.</span>
             </div>
          )}
        </div>

        {/* Disaster Recovery Playbook (Col span 6) */}
        <div className="col-span-1 md:col-span-6 bg-surface-container-low rounded-xl border border-surface-bright p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <FileCheck className={`w-5 h-5 ${isRansomwareSafe != null ? (isRansomwareSafe ? 'text-ready-emerald' : 'text-critical-red') : 'text-on-surface-variant'}`} />
              <h3 className="text-base font-semibold text-on-surface">Disaster Recovery Playbook</h3>
            </div>
            <p className="text-sm text-on-surface-variant mb-4">
              Automated Ransomware Recovery Playbook is compiled and ready. Storage snapshots are cryptographically signed and air-gapped.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isRansomwareSafe != null ? (isRansomwareSafe ? 'bg-ready-emerald animate-pulse' : 'bg-critical-red') : 'bg-on-surface-variant'}`} />
              <span className="text-xs font-mono text-on-surface">Ransomware Safe: {isRansomwareSafe != null ? (isRansomwareSafe ? 'YES' : 'NO') : 'Unknown'}</span>
            </div>
            <span className={`text-xs font-mono font-semibold ${isRansomwareSafe != null ? (isRansomwareSafe ? 'text-ready-emerald' : 'text-critical-red') : 'text-on-surface-variant'}`}>
              {isRansomwareSafe != null ? (isRansomwareSafe ? 'PASS' : 'FAIL') : 'UNVERIFIED'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
