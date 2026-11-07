import { CheckCheck, AlertTriangle, Eye } from 'lucide-react';
import type { DailyReadinessReport } from '../../../types/readiness';

/**
 * Compact "What we checked overnight" strip. Every pill is a check from
 * the report; counts are the report's own verification numbers.
 */
export function OvernightStrip({ report }: { report: DailyReadinessReport }) {
  const passed = report.passed_checks || [];
  const failed = report.failed_checks || [];
  const warnings = report.warnings || [];
  const verified = report.verification?.verified_items_count;
  const total = report.verification?.total_items_count;
  const hasCounts = typeof verified === 'number' && typeof total === 'number' && total > 0;
  const connectorCount = (report.connectors || []).length;
  const checkedAt = report.generated_at ? new Date(report.generated_at) : null;
  const checkedLabel =
    checkedAt && !Number.isNaN(checkedAt.getTime())
      ? checkedAt.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
      : null;

  const pills = [
    ...failed.map(c => ({ id: c.id || c.name, name: c.name, tone: 'failed' as const })),
    ...warnings.map(c => ({ id: c.id || c.name, name: c.name, tone: 'warning' as const })),
    ...passed.map(c => ({ id: c.id || c.name, name: c.name, tone: 'passed' as const })),
  ];

  const pillClass = {
    passed: 'border-ready-emerald/30 text-on-surface-variant',
    warning: 'border-drift-amber/40 text-on-surface',
    failed: 'border-critical-red/40 text-on-surface',
  };
  const dotClass = {
    passed: 'bg-ready-emerald',
    warning: 'bg-drift-amber',
    failed: 'bg-critical-red',
  };

  return (
    <section
      aria-label="What we checked overnight"
      className="bg-surface-container-low border border-surface-bright/60 rounded-2xl p-5 sm:p-6"
      data-testid="overnight-strip"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h2 className="text-sm font-bold text-on-surface flex items-center gap-2">
          <Eye className="w-4 h-4 text-ready-emerald" aria-hidden="true" />
          What we checked overnight
        </h2>
        <p className="text-xs text-on-surface-variant font-mono">
          {hasCounts ? `${verified} of ${total} checks passed` : 'Checks run on live data from your systems'}
          {connectorCount > 0 && ` · ${connectorCount} connected system${connectorCount === 1 ? '' : 's'}`}
          {checkedLabel && ` · as of ${checkedLabel}`}
        </p>
      </div>

      {pills.length === 0 ? (
        <p className="text-sm text-on-surface-variant">No checks have reported yet.</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {pills.map(p => (
            <li
              key={`${p.tone}-${p.id}`}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border bg-surface-container text-xs ${pillClass[p.tone]}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${dotClass[p.tone]}`} aria-hidden="true" />
              {p.name}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 pt-3 border-t border-surface-bright/60 flex flex-wrap gap-x-5 gap-y-1 text-[11px] font-mono text-on-surface-variant">
        <span className="inline-flex items-center gap-1.5"><CheckCheck className="w-3.5 h-3.5 text-ready-emerald" aria-hidden="true" />{passed.length} passed</span>
        <span className="inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5 text-drift-amber" aria-hidden="true" />{warnings.length} to watch</span>
        <span className="inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5 text-critical-red" aria-hidden="true" />{failed.length} did not pass</span>
      </div>
    </section>
  );
}
