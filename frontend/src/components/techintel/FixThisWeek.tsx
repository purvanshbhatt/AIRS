import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, Copy, ExternalLink, MapPin, Plug, ShieldCheck, Wrench } from 'lucide-react';
import { Chip, ExploitedBadge, MAX_FIX_ACTIONS, hostOf, whereText, type FixAction } from './shared';

function CopyForItButton({ text }: { text: string }) {
  const [state, setState] = useState<'idle' | 'copied' | 'manual'>('idle');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const copy = async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(text);
      setState('copied');
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setState('idle'), 2500);
    } catch {
      // Browser blocked the clipboard: show the message so it can be copied by hand.
      setState('manual');
    }
  };

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={copy}
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 transition-colors cursor-pointer"
        data-testid="copy-for-it"
      >
        {state === 'copied' ? <Check className="w-4 h-4" aria-hidden="true" /> : <Copy className="w-4 h-4" aria-hidden="true" />}
        {state === 'copied' ? 'Copied. Paste it into an email or chat' : 'Copy message for my IT person'}
      </button>
      <span className="sr-only" role="status">
        {state === 'copied' ? 'Message copied' : ''}
      </span>
      {state === 'manual' && (
        <label className="block">
          <span className="block text-xs text-on-surface-variant mb-1">
            Your browser blocked copying. Select this text and copy it:
          </span>
          <textarea
            readOnly
            value={text}
            rows={4}
            onFocus={e => e.currentTarget.select()}
            className="w-full rounded-xl border border-outline-variant bg-surface-container px-3 py-2 text-xs text-on-surface"
            data-testid="copy-for-it-text"
          />
        </label>
      )}
    </div>
  );
}

function FixCard({ action, index }: { action: FixAction; index: number }) {
  return (
    <li
      className={`rounded-2xl border border-l-4 bg-surface-container-low p-5 space-y-3 ${
        action.exploited ? 'border-critical-red/40' : 'border-drift-amber/40'
      }`}
      data-testid="fix-card"
    >
      <div className="flex items-start gap-3">
        <span
          className="w-7 h-7 rounded-lg bg-surface-container border border-outline-variant flex items-center justify-center text-xs font-mono font-bold text-on-surface-variant shrink-0"
          aria-hidden="true"
        >
          {index + 1}
        </span>
        <div className="min-w-0 space-y-1.5">
          <h3 className="text-base font-bold text-on-surface leading-snug" data-testid="fix-card-title">
            {action.title}
          </h3>
          {(action.exploited || action.endOfLife) && (
            <div className="flex flex-wrap items-center gap-1.5">
              {action.exploited && <ExploitedBadge />}
              {action.endOfLife && <Chip tone="warning">No longer supported</Chip>}
            </div>
          )}
        </div>
      </div>

      <p className="flex items-start gap-2 text-sm text-on-surface-variant" data-testid="fix-card-where">
        <MapPin className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
        <span className="min-w-0 break-words">{whereText(action)}</span>
      </p>

      <p className="flex items-start gap-2 text-sm text-on-surface" data-testid="fix-card-step">
        <Wrench className="w-4 h-4 shrink-0 mt-0.5 text-ready-emerald" aria-hidden="true" />
        <span className="min-w-0">
          <strong>Fix:</strong> {action.fixStep}
        </span>
      </p>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
        <CopyForItButton text={action.sendText} />
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
          {action.reference && (
            <span className="font-mono text-on-surface-variant/80" data-testid="fix-card-reference">
              {action.reference}
            </span>
          )}
          {action.sourceUrl && (
            <a
              href={action.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-semibold text-ready-emerald hover:underline"
              data-testid="fix-card-source"
            >
              Source: {hostOf(action.sourceUrl)}
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

interface FixThisWeekProps {
  actions: FixAction[];
  /** False when nothing is connected and no software is listed: we cannot say "all clear". */
  hasSource: boolean;
  onAddWebsite?: () => void;
}

/** The short action list that leads the page. Never more than five cards. */
export function FixThisWeek({ actions, hasSource, onAddWebsite }: FixThisWeekProps) {
  const list = (actions || []).slice(0, MAX_FIX_ACTIONS);

  return (
    <section className="space-y-4" aria-labelledby="fix-this-week-title" data-testid="fix-this-week">
      <div>
        <h2 id="fix-this-week-title" className="text-lg sm:text-xl font-bold tracking-tight text-on-surface">
          Fix this week
        </h2>
        <p className="text-sm text-on-surface-variant mt-0.5">
          {!hasSource
            ? 'We cannot tell you what to fix until we can see your software.'
            : list.length === 0
              ? 'Nothing confirmed needs fixing this week.'
              : 'Confirmed problems only, most urgent first. Each one has a message you can send straight to IT.'}
        </p>
      </div>

      {!hasSource ? (
        <div
          className="p-8 rounded-xl bg-surface-container-low border border-dashed border-outline-variant flex flex-col items-center text-center"
          data-testid="no-source-empty"
        >
          <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
            <Plug className="w-6 h-6" aria-hidden="true" />
          </div>
          <h3 className="text-base font-semibold text-on-surface">We cannot see your software yet</h3>
          <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
            No system that lists your software is connected, so nothing has been checked. This is not an all-clear.
            Connect one in Integrations and the fixes that matter show up here.
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/connectors"
              className="inline-flex items-center gap-2 px-6 py-3 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl transition-all active:scale-[0.98]"
              data-testid="no-source-integrations-link"
            >
              <Plug className="w-4 h-4" aria-hidden="true" />
              <span>Open Integrations</span>
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
            {onAddWebsite && (
              <button
                type="button"
                onClick={onAddWebsite}
                className="px-5 py-3 rounded-xl border border-outline-variant text-sm font-semibold text-on-surface hover:bg-surface-container cursor-pointer"
              >
                Add a website instead
              </button>
            )}
          </div>
        </div>
      ) : list.length === 0 ? (
        <div
          className="p-6 rounded-xl bg-surface-container-low border border-outline-variant flex items-start gap-3"
          data-testid="fix-this-week-clear"
        >
          <ShieldCheck className="w-5 h-5 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-sm text-on-surface leading-relaxed">
            No confirmed problem needs your time this week in the software we can see. Possible matches we could not
            verify are listed under "Everything we checked" below.
          </p>
        </div>
      ) : (
        <ol className="space-y-3 list-none p-0">
          {list.map((action, i) => (
            <FixCard key={action.id} action={action} index={i} />
          ))}
        </ol>
      )}
    </section>
  );
}

export default FixThisWeek;
