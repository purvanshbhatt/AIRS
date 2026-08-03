import React, { useEffect, useState } from 'react';
import { RecoveryReadinessBanner } from '../../components/readiness/RecoveryReadinessBanner';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { getDailyReadinessReport } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { ShieldAlert, Server, HardDrive, CheckCircle2 } from 'lucide-react';

export default function RecoveryReadinessPage() {
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = "default-org"; 

  const loadReport = async () => {
    setLoading(true);
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
    loadReport();
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-center gap-4 border-b border-slate-200 pb-6">
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recovery Readiness</h1>
          <p className="text-slate-500 mt-1">
            Validating business continuity and ransomware resilience.
          </p>
        </div>
      </div>

      <RecoveryReadinessBanner 
        canRecoverToday={report.business_continuity.can_recover_today}
        estimatedRecoveryHours={report.business_continuity.estimated_recovery_hours}
        lastBackupVerifiedAt={report.business_continuity.last_backup_verified_at}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border border-slate-200">
          <div className="flex items-center gap-3 mb-6">
            <Server className="w-5 h-5 text-emerald-500" />
            <h3 className="text-lg font-semibold text-slate-900">Verified Critical Systems</h3>
          </div>
          <ul className="space-y-3">
            {report.business_continuity.verified_systems.map((system, idx) => (
              <li key={idx} className="flex items-center gap-3 text-slate-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                {system}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-200">
          <div className="flex items-center gap-3 mb-6">
            <HardDrive className="w-5 h-5 text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-900">Assumed Dependencies</h3>
          </div>
          <ul className="space-y-3">
            {report.business_continuity.assumed_systems.map((system, idx) => (
              <li key={idx} className="flex items-center gap-3 text-slate-500">
                <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
                {system}
              </li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  );
}
