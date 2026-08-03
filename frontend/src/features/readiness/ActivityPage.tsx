import React, { useEffect, useState } from 'react';
import { LoadingState, ErrorState } from '../../components/readiness/ReadinessStates';
import { getDailyReadinessReport } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import { Activity as ActivityIcon, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function ActivityPage() {
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
