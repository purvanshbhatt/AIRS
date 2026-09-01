import React from 'react';
import { Cpu, AlertTriangle, ShieldCheck, ShieldAlert, AlertCircle } from 'lucide-react';
import { Card, CardContent, Badge } from '../ui';
import { TechInventoryItem } from '../../api';

interface InventoryTabProps {
  items: TechInventoryItem[];
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function InventoryTab({ items, isLoading, error, onRetry }: InventoryTabProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Loading technology inventory...</p>
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
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to load inventory</h4>
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
        <Cpu className="w-12 h-12 text-slate-350 dark:text-slate-700 mb-3 opacity-60" />
        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Empty Inventory</h4>
        <p className="text-xs text-slate-500 dark:text-slate-450 mt-1">No technology assets are currently registered in this estate.</p>
      </div>
    );
  }

  const getImpactBadge = (impact: string) => {
    switch (impact.toLowerCase()) {
      case 'critical':
      case 'high':
        return <Badge variant="critical" className="text-[10px] font-bold capitalize">{impact}</Badge>;
      case 'medium':
        return <Badge variant="drift" className="text-[10px] font-bold capitalize">{impact}</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] font-bold capitalize text-slate-500">{impact}</Badge>;
    }
  };

  return (
    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm overflow-hidden bg-white/60 dark:bg-slate-950/20">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 text-slate-500 uppercase tracking-wider font-bold">
              <th className="py-3 px-6">Component</th>
              <th className="py-3 px-6">Category</th>
              <th className="py-3 px-6">Version</th>
              <th className="py-3 px-6 text-center">Behind</th>
              <th className="py-3 px-6 text-center">CVE Status</th>
              <th className="py-3 px-6 text-center">KEVs</th>
              <th className="py-3 px-6 text-center">Readiness Impact</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20 transition-colors">
                <td className="py-4 px-6 font-sans font-bold text-slate-900 dark:text-slate-100">
                  {item.component_name}
                </td>
                <td className="py-4 px-6 font-sans text-slate-500 dark:text-slate-400 capitalize">
                  {item.category || 'Other'}
                </td>
                <td className="py-4 px-6 text-slate-700 dark:text-slate-350">
                  {item.version || '—'}
                </td>
                <td className="py-4 px-6 text-center font-bold text-slate-800 dark:text-slate-200">
                  {item.major_versions_behind} Major
                </td>
                <td className="py-4 px-6 text-center">
                  <div className="flex items-center justify-center gap-1.5 font-sans">
                    {item.critical_cves > 0 && (
                      <span className="px-1.5 py-0.5 text-[10px] rounded bg-red-500/10 text-red-500 border border-red-500/20 font-bold">
                        {item.critical_cves} Crit
                      </span>
                    )}
                    {item.high_cves > 0 && (
                      <span className="px-1.5 py-0.5 text-[10px] rounded bg-amber-500/10 text-amber-600 dark:text-amber-500 border border-amber-500/20 font-bold">
                        {item.high_cves} High
                      </span>
                    )}
                    {item.critical_cves === 0 && item.high_cves === 0 && (
                      <span className="px-1.5 py-0.5 text-[10px] rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-500 border border-emerald-500/20 font-bold">
                        Secure
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-4 px-6 text-center">
                  {item.kev_count > 0 ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-red-650/10 text-red-600 border border-red-600/30 text-[10px] font-sans font-black uppercase tracking-wider animate-pulse">
                      <ShieldAlert className="w-3 h-3" />
                      {item.kev_count} Active KEV
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400 dark:text-slate-650 font-bold">—</span>
                  )}
                </td>
                <td className="py-4 px-6 text-center font-sans">
                  {getImpactBadge(item.readiness_impact)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
export default InventoryTab;
