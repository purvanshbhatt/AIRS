import React from 'react';
import { Calendar, AlertCircle, AlertTriangle, ShieldCheck, Info } from 'lucide-react';
import { Card, CardContent, Badge } from '../ui';
import { TechLifecycleAnalysis } from '../../api';

interface LifecycleTabProps {
  items: TechLifecycleAnalysis[];
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function LifecycleTab({ items, isLoading, error, onRetry }: LifecycleTabProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Running lifecycle analysis...</p>
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
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to analyze lifecycle</h4>
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
        <Calendar className="w-12 h-12 text-slate-350 dark:text-slate-700 mb-3 opacity-60" />
        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">No Lifecycle Data</h4>
        <p className="text-xs text-slate-500 dark:text-slate-450 mt-1">Complete your tech inventory to view EOL and deprecation timelines.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'eol':
      case 'end_of_life':
        return <Badge variant="danger" className="text-[10px] font-bold uppercase">End Of Life</Badge>;
      case 'deprecated':
        return <Badge variant="warning" className="text-[10px] font-bold uppercase">Deprecated</Badge>;
      case 'supported':
      case 'active':
      case 'lts':
        return <Badge variant="success" className="text-[10px] font-bold uppercase">Supported</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] font-bold uppercase text-slate-500">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert panel for EOL items */}
      {items.some(item => item.status.toLowerCase() === 'eol' || item.status.toLowerCase() === 'end_of_life') && (
        <Card className="border border-red-500/30 bg-red-500/5 backdrop-blur-[6px] rounded-3xl p-5 text-left">
          <div className="flex items-start gap-4">
            <div className="p-2.5 bg-red-500/10 rounded-2xl border border-red-500/20">
              <AlertCircle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h4 className="text-sm font-black text-red-500 uppercase tracking-wider">CRITICAL LIFECYCLE VULNERABILITY</h4>
              <p className="text-xs text-slate-650 dark:text-slate-350 mt-1 leading-relaxed font-semibold">
                You have active components running on End-of-Life (EOL) versions. These components no longer receive security patches, and their presence induces a compliance score penalty. Action is required.
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm overflow-hidden bg-white/60 dark:bg-slate-950/20">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 text-slate-500 uppercase tracking-wider font-bold">
                <th className="py-3 px-6">Component</th>
                <th className="py-3 px-6">Current Version</th>
                <th className="py-3 px-6">Latest Supported</th>
                <th className="py-3 px-6">EOL Date</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6">Analysis Findings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20 transition-colors">
                  <td className="py-4 px-6 font-sans font-bold text-slate-900 dark:text-slate-100">
                    {item.component_name}
                  </td>
                  <td className="py-4 px-6 text-slate-700 dark:text-slate-350">
                    {item.version}
                  </td>
                  <td className="py-4 px-6 text-slate-700 dark:text-slate-350">
                    {item.latest_supported || 'Unknown'}
                  </td>
                  <td className="py-4 px-6 text-slate-500 dark:text-slate-400">
                    {item.eol_date ? new Date(item.eol_date).toLocaleDateString() : 'Continuous Support'}
                  </td>
                  <td className="py-4 px-6 font-sans">
                    {getStatusBadge(item.status)}
                  </td>
                  <td className="py-4 px-6 font-sans text-slate-650 dark:text-slate-400 font-semibold leading-relaxed">
                    {item.message}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
export default LifecycleTab;
