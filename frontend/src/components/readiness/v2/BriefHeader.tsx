import { Link } from 'react-router-dom';
import { FileText, Plug } from 'lucide-react';

/**
 * Header row for the V2 morning brief: org name, date, and the two
 * actions a director reaches for most (export the 1-page report, connect
 * a system). The date comes from the report when available.
 */
export function BriefHeader({
  orgName,
  date,
  isDemo = false,
}: {
  orgName: string;
  /** ISO string (report.generated_at) or undefined. */
  date?: string;
  isDemo?: boolean;
}) {
  const parsed = date ? new Date(date) : new Date();
  const safeDate = Number.isNaN(parsed.getTime()) ? new Date() : parsed;
  const dateLabel = safeDate.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between" data-testid="brief-header">
      <div className="min-w-0">
        <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
          Morning brief
          {isDemo && <span className="ml-2 text-drift-amber">Sandbox</span>}
        </p>
        <h1 className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-on-surface truncate" data-testid="brief-org-name">
          {orgName}
        </h1>
        <p className="mt-1 text-sm text-on-surface-variant" data-testid="brief-date">
          {dateLabel}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <Link
          to="/reports"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl bg-surface-container-high border border-outline-variant/40 text-on-surface hover:bg-surface-bright transition-colors"
        >
          <FileText className="w-4 h-4 text-ready-emerald" aria-hidden="true" />
          <span>Export 1-page report</span>
        </Link>
        <Link
          to="/connectors"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl bg-surface-container-high border border-outline-variant/40 text-on-surface hover:bg-surface-bright transition-colors"
        >
          <Plug className="w-4 h-4 text-ready-emerald" aria-hidden="true" />
          <span>Connect a system</span>
        </Link>
      </div>
    </header>
  );
}
