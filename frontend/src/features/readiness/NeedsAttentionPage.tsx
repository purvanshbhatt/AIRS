import React, { useEffect, useState } from 'react';
import { StatusCard } from '../../components/readiness/StatusCard';
import { LoadingState, ErrorState, HealthyState } from '../../components/readiness/ReadinessStates';
import { getDailyReadinessReport, triggerProblemFix } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { Zap } from 'lucide-react';

export default function NeedsAttentionPage() {
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = "default-org"; 

  const loadReport = async () => {
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
    loadReport();
  }, []);

  const handleFix = async (problemId: string) => {
    await triggerProblemFix(problemId);
    await loadReport();
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-center gap-4 border-b border-slate-200 pb-6">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center">
          <Zap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Needs Attention</h1>
          <p className="text-slate-500 mt-1">
            {report.immediate_actions.length} items require your review today.
          </p>
        </div>
      </div>

      <section>
        {report.immediate_actions.length === 0 ? (
          <HealthyState />
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {report.immediate_actions.map(action => (
              <StatusCard key={action.id} variant="story" action={action} onFix={handleFix} />
            ))}
          </div>
        )}
      </section>

    </div>
  );
}
