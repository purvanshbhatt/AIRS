import React from 'react';
import { ShieldX, ShieldAlert, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';
import { Card, Badge } from '../ui';
import { TechExposureItem } from '../../api';

interface ExposureTabProps {
  items: TechExposureItem[];
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function ExposureTab({ items, isLoading, error, onRetry }: ExposureTabProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Scanning vulnerability catalogs...</p>
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
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to run vulnerability scan</h4>
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
      <div className="flex flex-col items-center justify-center py-20 text-center px-4 space-y-3">
        <div className="p-3 bg-[#00C853]/10 rounded-full">
          <CheckCircle className="w-8 h-8 text-[#00C853]" />
        </div>
        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Estate Clean & Secure</h4>
        <p className="text-xs text-slate-500 dark:text-slate-450">No known vulnerabilities or active KEVs detected on tracked components.</p>
      </div>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <Badge variant="danger" className="text-[10px] font-bold uppercase bg-red-600">Critical</Badge>;
      case 'high':
        return <Badge variant="danger" className="text-[10px] font-bold uppercase">High</Badge>;
      case 'medium':
        return <Badge variant="warning" className="text-[10px] font-bold uppercase">Medium</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] font-bold uppercase text-slate-500">{severity}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert banner for KEVs */}
      {items.some(item => item.is_kev) && (
        <Card className="border border-red-650/30 bg-red-650/5 backdrop-blur-[6px] rounded-3xl p-5 text-left">
          <div className="flex items-start gap-4">
            <div className="p-2.5 bg-red-600/10 rounded-2xl border border-red-600/20">
              <ShieldAlert className="w-6 h-6 text-red-650" />
            </div>
            <div>
              <h4 className="text-sm font-black text-red-600 uppercase tracking-wider">KNOWN EXPLOITED VULNERABILITY (KEV) ALERT</h4>
              <p className="text-xs text-slate-650 dark:text-slate-350 mt-1 leading-relaxed font-semibold">
                One or more components are exposed to vulnerabilities listed on the CISA KEV Catalog. These vulnerabilities are actively exploited in the wild. Remediation or isolation is required immediately to prevent compromised states.
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
                <th className="py-3 px-6">CVE ID</th>
                <th className="py-3 px-6">Component Name</th>
                <th className="py-3 px-6">Detected Version</th>
                <th className="py-3 px-6">Severity Rating</th>
                <th className="py-3 px-6 text-center">Exploit Status</th>
                <th className="py-3 px-6 text-right">Reference Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20 transition-colors">
                  <td className="py-4 px-6 font-bold text-slate-900 dark:text-slate-100">
                    {item.cve_id}
                  </td>
                  <td className="py-4 px-6 font-sans font-bold text-slate-700 dark:text-slate-350">
                    {item.component_name}
                  </td>
                  <td className="py-4 px-6 text-slate-600 dark:text-slate-400">
                    {item.version}
                  </td>
                  <td className="py-4 px-6 font-sans">
                    {getSeverityBadge(item.severity)}
                  </td>
                  <td className="py-4 px-6 text-center">
                    {item.is_kev ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-red-650/10 text-red-650 border border-red-650/30 text-[10px] font-sans font-extrabold uppercase tracking-wide animate-pulse">
                        <ShieldAlert className="w-3 h-3 text-red-600" />
                        ACTIVE KEV
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500 dark:text-slate-500 font-semibold font-sans">No Active Exploit</span>
                    )}
                  </td>
                  <td className="py-4 px-6 text-right font-sans">
                    <a
                      href={`https://nvd.nist.gov/vuln/detail/${item.cve_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-bold text-indigo-500 hover:text-indigo-650 dark:hover:text-indigo-400"
                    >
                      NVD Page
                      <ExternalLink className="w-3 h-3" />
                    </a>
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
export default ExposureTab;
