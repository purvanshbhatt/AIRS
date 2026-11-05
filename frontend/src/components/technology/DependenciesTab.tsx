import React from 'react';
import { Network, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../ui';
import { FrameworkCoverageItem } from '../../api';

interface DependenciesTabProps {
  items: FrameworkCoverageItem[];
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function DependenciesTab({ items, isLoading, error, onRetry }: DependenciesTabProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Analyzing framework dependencies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-4 space-y-4">
        <div className="p-3 bg-danger-500/10 rounded-full">
          <AlertTriangle className="h-8 w-8 text-danger-500" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to load coverage mapping</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error}</p>
        </div>
        {onRetry && (
          <button onClick={onRetry} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold rounded-lg transition-colors">
            Retry Connection
          </button>
        )}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-4">
        <Network className="w-12 h-12 text-slate-350 dark:text-slate-700 mb-3 opacity-60" />
        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">No Coverage Data</h4>
        <p className="text-xs text-slate-500 dark:text-slate-450 mt-1">Configure compliance frameworks to see controls mapping and coverage metrics.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {items.map((item, idx) => {
        const isComplete = item.coverage_percent === 100;
        const colorClass = isComplete 
          ? 'text-[#00C853] bg-[#00C853]/10 border-[#00C853]/20' 
          : item.coverage_percent > 60 
          ? 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20' 
          : 'text-amber-600 bg-amber-500/10 border-amber-500/20';

        return (
          <Card key={idx} className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 hover:shadow-md transition-all duration-300">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
                  {item.framework}
                </CardTitle>
                <Badge className={`${colorClass} text-[10px] font-bold`}>
                  {item.coverage_percent.toFixed(0)}% Covered
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Coverage details */}
              <div className="flex items-center justify-between text-xs font-bold text-slate-500 dark:text-slate-400">
                <span>VERIFIED CONTROLS</span>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  {item.covered_controls} / {item.total_controls} Controls
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-100 dark:bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-200/50 dark:border-slate-800/50">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    isComplete ? 'bg-[#00C853]' : item.coverage_percent > 60 ? 'bg-indigo-500' : 'bg-[#D97706]'
                  }`} 
                  style={{ width: `${item.coverage_percent}%` }}
                />
              </div>

              {/* Visual Gaps highlight */}
              <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between text-[11px] font-semibold text-slate-500">
                {isComplete ? (
                  <span className="flex items-center gap-1 text-[#00C853]">
                    <CheckCircle2 className="w-3.5 h-3.5" /> All controls verified
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-slate-650 dark:text-slate-400">
                    Gaps detected: {item.total_controls - item.covered_controls} controls outstanding
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
export default DependenciesTab;
