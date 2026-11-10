import React from 'react';
import { Loader2, RefreshCw, AlertTriangle, CheckCircle2, Eye, EyeOff, Clock } from 'lucide-react';
import type { StackRefreshResult } from '../../api';
import { TechnicalDetails } from '../readiness/PlainLanguage';
import { Chip, coverageText, formatDateTime, plural, timeAgo, type CoverageView } from './shared';

export interface RefreshState {
  running: boolean;
  result: StackRefreshResult | null;
  error: { message: string; detail?: string } | null;
}

interface OverviewStripProps {
  coverage: CoverageView;
  /** When the check last ran (`as_of`). */
  asOf: string | null;
  /** True when the security feeds could not be refreshed and older results are shown. */
  stale?: boolean;
  demo?: boolean;
  refresh: RefreshState;
  onRefresh: () => void;
}

/**
 * Sits directly under the "Fix this week" list: what was checked, what could
 * not be seen, when, and the "Check now" button. No totals.
 */
export function OverviewStrip({ coverage, asOf, stale = false, demo = false, refresh, onRefresh }: OverviewStripProps) {
  const ago = timeAgo(asOf);
  const text = coverageText(coverage);

  return (
    <section
      className="bg-surface-container-low rounded-2xl border border-outline-variant p-4 sm:p-5 space-y-3"
      aria-label="What was checked"
      data-testid="techintel-overview"
    >
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div className="min-w-0 space-y-1.5 text-sm" data-testid="coverage-line">
          <p className="flex items-start gap-2 text-on-surface">
            <Eye className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
            <span className="min-w-0 break-words" data-testid="coverage-checked">{text.checked}</span>
          </p>
          <p className="flex items-start gap-2 text-on-surface-variant">
            <EyeOff className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            <span className="min-w-0 break-words" data-testid="coverage-unseen">{text.unseen}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 shrink-0">
          {demo && (
            <Chip testId="example-data-chip" title="This workspace shows example data, not your own systems">
              Example data
            </Chip>
          )}
          <p
            className="inline-flex items-center gap-1.5 text-xs text-on-surface-variant"
            data-testid="last-checked"
            title={formatDateTime(asOf) || undefined}
          >
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            {ago ? `Last checked ${ago}` : 'Not checked yet'}
          </p>
          <button
            type="button"
            onClick={onRefresh}
            disabled={refresh.running}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-outline-variant text-sm font-semibold text-on-surface hover:bg-surface-container transition-colors disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            data-testid="check-now"
          >
            {refresh.running ? (
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
            )}
            {refresh.running ? 'Checking...' : 'Check now'}
          </button>
        </div>
      </div>

      {stale && (
        <p className="flex items-start gap-2 text-xs text-drift-amber" data-testid="stale-note">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            The security feed could not be refreshed, so this shows the last results we have. Newer problems may be
            missing.
          </span>
        </p>
      )}

      <div aria-live="polite" className="space-y-3 empty:hidden">
        {refresh.running && (
          <p className="flex items-center gap-2 text-sm text-on-surface-variant" data-testid="refresh-progress">
            <Loader2 className="w-4 h-4 animate-spin text-ready-emerald" aria-hidden="true" />
            Comparing your software against the public security databases. This can take a minute.
          </p>
        )}

        {!refresh.running && refresh.error && (
          <div
            className="flex items-start gap-2 rounded-xl border border-critical-red/30 bg-critical-red/10 p-3 text-sm text-on-surface"
            role="alert"
            data-testid="refresh-error"
          >
            <AlertTriangle className="w-4 h-4 text-critical-red shrink-0 mt-0.5" aria-hidden="true" />
            <div className="min-w-0">
              <p className="font-semibold">{refresh.error.message}</p>
              {refresh.error.detail && (
                <p className="mt-1 text-[11px] font-mono text-on-surface-variant break-words">{refresh.error.detail}</p>
              )}
            </div>
          </div>
        )}

        {!refresh.running && refresh.result && (
          <div className="space-y-3" data-testid="refresh-result">
            <p className="flex items-start gap-2 text-sm text-on-surface">
              <CheckCircle2 className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
              <span>Check finished. The list above is up to date.</span>
            </p>
            {(refresh.result.errors || []).length > 0 && (
              <div className="rounded-xl border border-drift-amber/30 bg-drift-amber/10 p-3" data-testid="refresh-warnings">
                <p className="flex items-start gap-2 text-sm font-semibold text-on-surface">
                  <AlertTriangle className="w-4 h-4 text-drift-amber shrink-0 mt-0.5" aria-hidden="true" />
                  {plural(refresh.result.errors.length, 'lookup', 'lookups')} did not finish, so some programs may be
                  missing results. Try "Check now" again in a few minutes.
                </p>
                <TechnicalDetails title="What went wrong" hint="for your IT provider" className="mt-3" testId="refresh-error-details">
                  <ul className="space-y-1 text-[11px] font-mono text-on-surface-variant break-words">
                    {refresh.result.errors.map((e, i) => (
                      <li key={`${e}-${i}`}>{e}</li>
                    ))}
                  </ul>
                </TechnicalDetails>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default OverviewStrip;
