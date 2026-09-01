import React, { useEffect, useState } from 'react';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { getDailyReadinessReport } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import { Link } from 'react-router-dom';
import { Activity as ActivityIcon, CheckCircle2, AlertTriangle, ShieldCheck, Building, ArrowRight } from 'lucide-react';

export default function ActivityPage() {
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
              Create an organization to establish continuous audit activity logs and event histories.
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

  // Group timeline by category
  const groupedEvents = report.timeline.reduce((acc, event) => {
    const cat = event.category || 'today';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(event);
    return acc;
  }, {} as Record<string, typeof report.timeline>);

  const renderIcon = (type: string) => {
    switch (type) {
      case 'verified': return <ShieldCheck className="w-5 h-5 text-emerald-500" />;
      case 'action_taken': return <CheckCircle2 className="w-5 h-5 text-blue-500" />;
      case 'alert': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default: return <ActivityIcon className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="activity" />
      
      <div className="flex items-center gap-4 border-b border-slate-200 pb-6">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
          <ActivityIcon className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Activity</h1>
          <p className="text-slate-500 mt-1">
            Recent changes and their impact on your readiness.
          </p>
        </div>
      </div>

      <div className="space-y-12">
        {['today', 'yesterday', 'last_week'].map(category => {
          const events = groupedEvents[category];
          if (!events || events.length === 0) return null;
          
          return (
            <div key={category} className="space-y-4">
              <h2 className="text-sm font-bold tracking-wider text-slate-400 uppercase border-b border-slate-100 pb-2">
                {category.replace('_', ' ')}
              </h2>
              <div className="space-y-6 pl-2">
                {events.map((event, idx) => (
                  <div key={idx} className="flex gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {renderIcon(event.type)}
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-slate-900">{event.event}</h4>
                      {event.impact && (
                        <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                          {event.impact}
                        </p>
                      )}
                      <p className="text-xs text-slate-400 mt-2 font-medium">{event.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
