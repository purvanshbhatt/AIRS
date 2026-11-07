import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, UserCog, Send, ChevronRight } from 'lucide-react';
import type { ActionCard } from '../../../types/readiness';
import { normalizeAction, guidanceForAction } from '../PlainLanguage';

/**
 * One "What needs attention" card: What happened / Why it matters /
 * Who fixes it / How long, then the action. All copy comes from the
 * action card and the deterministic PlainLanguage guidance.
 */
export function AttentionCard({
  action,
  index,
  fixing,
  onFix,
}: {
  action: ActionCard;
  index: number;
  fixing: boolean;
  onFix: (id: string) => void;
}) {
  const item = normalizeAction(action, index);
  const guidance = guidanceForAction(item);
  const canFixNow = (action as { fix_now_available?: boolean }).fix_now_available !== false;
  const severity = String(item.severity || '').toLowerCase();
  const severityTone =
    severity === 'critical' || severity === 'high'
      ? 'text-critical-red bg-critical-red/10 border-critical-red/30'
      : 'text-drift-amber bg-drift-amber/10 border-drift-amber/30';

  return (
    <article
      className="bg-surface-container-low border border-surface-bright/60 rounded-2xl p-5 sm:p-6 m3-elevation-1"
      data-testid="attention-card"
    >
      <div className="flex flex-col lg:flex-row lg:items-start gap-5">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono font-bold uppercase tracking-wider ${severityTone}`}>
              <AlertTriangle className="w-3 h-3" aria-hidden="true" />
              {item.severity ? `${item.severity} priority` : 'Needs attention'}
            </span>
            <span className="text-[11px] text-on-surface-variant">{guidance.plainCategory}</span>
            {item.lastVerifiedAt && (
              <span className="text-[11px] font-mono text-on-surface-variant/70">Checked {item.lastVerifiedAt}</span>
            )}
          </div>

          <h3 className="text-lg font-bold text-on-surface tracking-tight">{item.title}</h3>

          <dl className="mt-3 space-y-2.5 text-sm">
            <div>
              <dt className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">What happened</dt>
              <dd className="text-on-surface leading-relaxed mt-0.5">{guidance.whatHappened}</dd>
            </div>
            <div>
              <dt className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">Why it matters</dt>
              <dd className="text-on-surface-variant leading-relaxed mt-0.5">{guidance.whyItMatters}</dd>
            </div>
          </dl>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs" data-testid="check-owner-strip">
            <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-surface-bright/40">
              <UserCog className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
              <span className="text-on-surface-variant">
                <strong className="text-on-surface block">Who fixes it</strong>
                {guidance.whoFixes}
              </span>
            </div>
            <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-surface-bright/40">
              <Clock className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
              <span className="text-on-surface-variant">
                <strong className="text-on-surface block">How long</strong>
                {guidance.howLong}
              </span>
            </div>
          </div>
        </div>

        <div className="lg:w-48 shrink-0 flex flex-col gap-2 lg:pt-1">
          {canFixNow ? (
            <button
              type="button"
              onClick={() => onFix(item.id)}
              disabled={fixing}
              className="inline-flex items-center justify-center px-5 py-3 rounded-xl bg-ready-emerald text-slate-950 font-bold text-sm hover:bg-ready-emerald/90 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {fixing ? 'Working...' : 'Fix now'}
            </button>
          ) : (
            <Link
              to="/operations"
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-surface-container-high border border-outline-variant/40 text-on-surface font-bold text-sm hover:bg-surface-bright transition-colors"
            >
              <Send className="w-4 h-4 text-ready-emerald" aria-hidden="true" />
              Send to IT / MSP
            </Link>
          )}
          {item.recommendation && (
            <p className="text-xs text-on-surface-variant leading-relaxed">
              <span className="font-semibold text-on-surface">What to do: </span>
              {item.recommendation}
            </p>
          )}
          <Link to="/needs-attention" className="inline-flex items-center gap-1 text-xs font-semibold text-ready-emerald hover:underline">
            Full details
            <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </article>
  );
}
