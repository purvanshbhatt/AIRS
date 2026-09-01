import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';
import { tokens } from '../../lib/design-tokens';
import { TrustBadge } from '../readiness/TrustBadge';

export interface MetricItem {
  label: string;
  value: string | number;
  status?: 'good' | "drift" | 'error' | 'neutral';
  subtitle?: string;
}

export interface SummaryCardProps {
  domainName: string;
  status?: 'ready' | "drift" | 'error' | 'healthy';
  readinessScore?: number;
  soWhat: string; // Business answer ("So what?")
  lastVerifiedText?: string;
  keyMetrics?: MetricItem[];
  icon?: React.ElementType;
  actions?: React.ReactNode;
  className?: string;
}

export function SummaryCard({
  domainName,
  status = 'ready',
  readinessScore = 0,
  soWhat,
  lastVerifiedText = 'Unable to Verify',
  keyMetrics = [],
  icon: Icon = ShieldCheck,
  actions,
  className,
}: SummaryCardProps) {
  const statusToken = status === 'error' ? tokens.status.error :
                      status === "drift" ? tokens.status.warning :
                      tokens.status.ready;

  const StatusIcon = status === 'error' ? AlertOctagon :
                     status === "drift" ? AlertTriangle :
                     CheckCircle2;

  return (
    <div className={cn(
      tokens.surface.base,
      "p-6 sm:p-8 shadow-sm transition-all border border-slate-200/80 dark:border-slate-800",
      className
    )}>
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-12 h-12 rounded-2xl flex items-center justify-center border shrink-0",
            statusToken.bg,
            statusToken.border,
            statusToken.text
          )}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {domainName}
              </h2>
              <TrustBadge status="verified" text={`${readinessScore}% Readiness`} />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5 font-medium">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              {lastVerifiedText}
            </p>
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-3 shrink-0">
            {actions}
          </div>
        )}
      </div>

      {/* Business Answer ("So What?") Section */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-black tracking-wider uppercase px-2.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/50">
            SO WHAT? — Executive Business Answer
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800/80">
          <p className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 leading-relaxed">
            {soWhat}
          </p>
        </div>
      </div>

      {/* Key Metrics Grid */}
      {keyMetrics.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {keyMetrics.map((metric, index) => {
            const metricStatusClass =
              metric.status === 'error' ? 'text-rose-600 dark:text-rose-400 bg-rose-50/50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30' :
              metric.status === "drift" ? 'text-amber-600 dark:text-amber-400 bg-amber-50/50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30' :
              metric.status === 'good' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/30' :
              'text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800';

            return (
              <div 
                key={index} 
                className={cn("p-3.5 rounded-xl border flex flex-col justify-between", metricStatusClass)}
              >
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 tracking-wide uppercase">
                  {metric.label}
                </span>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                    {metric.value}
                  </span>
                  {metric.subtitle && (
                    <span className="text-xs text-slate-400 font-normal">{metric.subtitle}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default SummaryCard;
