import React, { useEffect, useState } from 'react';
import { NorthStarHero } from '../../components/readiness/NorthStarHero';
import { ExecutiveQuestionsGrid } from '../../components/readiness/ExecutiveQuestionsGrid';
import { StatusCard } from '../../components/readiness/StatusCard';
import { ReadinessJourney } from '../../components/readiness/ReadinessJourney';
import { RecoveryReadinessBanner } from '../../components/readiness/RecoveryReadinessBanner';
import { LoadingState, ErrorState, HealthyState } from '../../components/readiness/ReadinessStates';
import { CoverageModal } from '../../components/readiness/CoverageModal';
import { getDailyReadinessReport, triggerProblemFix } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { ArrowRight, Activity, ShieldCheck, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function TodayPage() {
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coverageModalOpen, setCoverageModalOpen] = useState(false);

  // In a real app, orgId would come from a context or params
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
    // Reload report to get fresh state
    await loadReport();
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  return (
    <div className="space-y-12 animate-in fade-in duration-500">
      
      {/* SECTION 1: North Star Hero (Good Morning) */}
      <section>
        <NorthStarHero 
          status={report.status}
          confidencePct={report.verification.overall_confidence_pct}
          verifiedSystemsCount={report.verification.verified_items_count}
          morningBrief={report.summary}
          trendText={report.trend.narrative}
        />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12">
        <div className="lg:col-span-2 space-y-12">
          {/* Readiness Journey (Replaces Executive Grid as the Morning Brief story) */}
          <section>
            <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-500" />
              Morning Brief
            </h2>
            <ReadinessJourney />
          </section>

          {/* SECTION 3: Needs Attention */}
          <section className="space-y-4">
            <div className="flex items-center justify-between ml-2 mr-2">
              <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">
                Items Requiring Attention
              </h3>
              {report.immediate_actions.length > 0 && (
                <Link to="/readiness/actions" className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1">
                  View All <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
            
            {report.immediate_actions.length === 0 ? (
              <HealthyState />
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {report.immediate_actions.slice(0, 3).map(action => (
                  <StatusCard key={action.id} variant="story" action={action} onFix={handleFix} />
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="space-y-8">
          {/* SECTION 2: Here's Why (Executive Questions) */}
          <section className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase ml-2">Executive Summary</h3>
            <ExecutiveQuestionsGrid 
              canOperate={report.business_continuity.can_operate_today}
              canRecover={report.business_continuity.can_recover_today}
              itemsNeedingAttention={report.immediate_actions.length + report.failed_checks.length}
              confidencePct={report.verification.overall_confidence_pct}
            />
          </section>

          {/* SECTION 4: Recovery Readiness */}
          <section className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase ml-2">Recovery Readiness</h3>
            <RecoveryReadinessBanner 
              canRecoverToday={report.business_continuity.can_recover_today}
              estimatedRecoveryHours={report.business_continuity.estimated_recovery_hours}
              lastBackupVerifiedAt={report.business_continuity.last_backup_verified_at}
            />
          </section>
        </div>
      </div>

      {/* SECTION 5: Recent Changes & Coverage */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Coverage Card */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5 text-slate-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">What We Can Verify</h3>
            <p className="text-slate-600 text-sm mb-6">
              We have direct telemetry from {report.coverage.overall_percentage}% of your critical environment.
            </p>
          </div>
          <button 
            onClick={() => setCoverageModalOpen(true)}
            className="text-sm font-medium text-slate-900 border border-slate-200 rounded-xl py-2.5 px-4 hover:bg-slate-50 transition-colors w-full flex justify-center items-center gap-2"
          >
            View Details <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Recent Activity Card */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Activity className="w-5 h-5 text-slate-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Recent Changes</h3>
            <p className="text-slate-600 text-sm mb-6">
              {report.timeline.length > 0 ? report.timeline[0].event : "No recent changes detected."}
            </p>
          </div>
          <Link 
            to="/readiness/activity"
            className="text-sm font-medium text-slate-900 border border-slate-200 rounded-xl py-2.5 px-4 hover:bg-slate-50 transition-colors w-full flex justify-center items-center gap-2"
          >
            View Full Activity <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

      </section>

      <CoverageModal 
        isOpen={coverageModalOpen} 
        onClose={() => setCoverageModalOpen(false)} 
        coverage={report.coverage} 
      />

    </div>
  );
}
