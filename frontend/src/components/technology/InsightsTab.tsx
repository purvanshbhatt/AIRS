import React from 'react';
import { Lightbulb, ShieldAlert, Sparkles, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui';

export function InsightsTab() {
  const recommendations = [
    {
      title: 'Remediate OpenSSL CVE-2024-9143',
      priority: 'CRITICAL',
      effort: 'Low (15 min patch)',
      description: 'An active KEV is present in your OpenSSL package. Upgrading to OpenSSL 3.4.0 will restore 4.0 readiness points immediately.',
      remediation: 'Run apt-get update && apt-get install --only-upgrade openssl in production build files.',
    },
    {
      title: 'Upgrade Python Runtime to 3.12+',
      priority: 'MEDIUM',
      effort: 'Medium (1 day migration)',
      description: 'Python 3.9 will reach EOL in October 2026. Upgrading now prevents post-EOL security drift.',
      remediation: 'Update Dockerfile base image to python:3.12-slim and run validation pipeline tests.',
    },
    {
      title: 'Establish Postgres Version Baseline',
      priority: 'LOW',
      effort: 'Low (no-op config lock)',
      description: 'Production nodes are running stable PostgreSQL 17, but config files lack an explicit version pinning lock.',
      remediation: 'Add postgres:17.2-alpine spec to docker-compose and deployment manifests.',
    },
  ];

  return (
    <div className="space-y-6 text-left">
      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 shadow-sm p-6">
        <CardHeader className="p-0 pb-4 mb-4 border-b border-slate-200/60 dark:border-slate-800/60">
          <CardTitle className="text-base font-extrabold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            AI-Driven Governance Insights
          </CardTitle>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
            Auto-synthesized recommendations from the ResilAI telemetry agent.
          </p>
        </CardHeader>
        <CardContent className="p-0 space-y-4">
          {recommendations.map((rec, idx) => {
            const isCritical = rec.priority === 'CRITICAL';
            return (
              <div 
                key={idx} 
                className={`p-4 rounded-2xl border ${
                  isCritical 
                    ? 'border-red-500/20 bg-red-500/5 dark:bg-red-950/10' 
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/10'
                } flex flex-col md:flex-row md:items-start justify-between gap-4`}
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg ${
                      isCritical ? 'bg-red-500/15 text-red-500' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}>
                      {rec.priority} PRIORITY
                    </span>
                    <span className="text-[10px] text-slate-400 font-bold uppercase font-mono">
                      EFFORT: {rec.effort}
                    </span>
                  </div>
                  <h4 className="text-sm font-black text-slate-905 dark:text-slate-100">
                    {rec.title}
                  </h4>
                  <p className="text-xs text-slate-650 dark:text-slate-400 leading-relaxed font-semibold">
                    {rec.description}
                  </p>
                  <div className="bg-white/40 dark:bg-slate-950/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/50 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                    <span className="font-bold text-slate-900 dark:text-slate-250 block mb-1">REMEDIATION STEPS:</span>
                    {rec.remediation}
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
export default InsightsTab;
