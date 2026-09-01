import React from 'react';
import { History, ShieldAlert, ShieldCheck, ArrowUpCircle, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui';

export function TimelineTab() {
  const events = [
    {
      date: '2026-05-18',
      title: 'Python Version Upgrade',
      description: 'Upgraded backend environment from Python 3.9 (EOL in 5 months) to Python 3.12 (Supported LTS). Resolved EOL warning.',
      type: 'upgrade',
      impact: '+3.5 Readiness Points',
    },
    {
      date: '2026-05-14',
      title: 'Active Exploited CVE Detected',
      description: 'CISA KEV vulnerability CVE-2024-9143 detected on OpenSSL 3.0.1. Mitigations in progress.',
      type: 'cve',
      impact: '-4.0 Readiness Points',
    },
    {
      date: '2026-05-10',
      title: 'Wazuh Agent Deployment',
      description: 'Deployed Wazuh telemetry client to 4 new production database nodes. Automated control verification activated.',
      type: 'telemetry',
      impact: '+2.0 Readiness Points',
    },
    {
      date: '2026-05-02',
      title: 'PostgreSQL Baseline Migration',
      description: 'Completed migration of production cache database to PostgreSQL 17 (Stable LTS). Resolved deprecated versions risk.',
      type: 'upgrade',
      impact: '+5.0 Readiness Points',
    },
  ];

  return (
    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 shadow-sm p-6 text-left">
      <CardHeader className="p-0 pb-4 mb-4 border-b border-slate-200/60 dark:border-slate-800/60">
        <CardTitle className="text-base font-extrabold flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-500" />
          Technology Change Ledger & Timeline
        </CardTitle>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
          Audit trail of technology stack updates, version adjustments, and vulnerability alert occurrences.
        </p>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative border-l border-slate-200 dark:border-slate-800 ml-3.5 pl-6 space-y-8 py-2">
          {events.map((event, idx) => {
            const isNegative = event.type === 'cve';
            return (
              <div key={idx} className="relative">
                {/* Timeline node dot */}
                <span className={`absolute -left-[31px] top-1.5 flex h-4 w-4 items-center justify-center rounded-full border bg-white dark:bg-slate-950 ${
                  isNegative ? 'border-red-500 text-red-500' : 'border-[#00C853] text-[#00C853]'
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${isNegative ? 'bg-red-500' : 'bg-[#00C853]'}`} />
                </span>

                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 font-mono">
                      {event.date}
                    </span>
                    <h4 className="text-xs font-black text-slate-900 dark:text-slate-100 mt-0.5">
                      {event.title}
                    </h4>
                    <p className="text-xs text-slate-650 dark:text-slate-400 mt-1 leading-relaxed max-w-xl font-semibold">
                      {event.description}
                    </p>
                  </div>
                  <span className={`text-xs font-bold font-mono px-2.5 py-0.5 rounded-lg shrink-0 ${
                    isNegative ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-[#00C853]/10 text-[#00C853] border border-[#00C853]/20'
                  }`}>
                    {event.impact}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
export default TimelineTab;
