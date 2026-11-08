import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, ChevronDown, ClipboardCopy, X } from 'lucide-react';
import { getConnectorsList } from '../../api';
import type { DailyReadinessReport } from '../../types/readiness';
import type { FirstRunItem } from '../../types/onboarding';
import { FIRST_RUN_COPY, FIRST_RUN_DISMISSED_KEY, IT_HANDOFF_NOTE } from '../onboarding/onboardingData';

interface FirstRunChecklistProps {
  orgId: string;
  report: DailyReadinessReport | null;
  /** Demo workspaces never show the checklist. */
  isDemo?: boolean;
}

const TOTAL = 3;

function readDismissed(orgId: string): boolean {
  try {
    return localStorage.getItem(FIRST_RUN_DISMISSED_KEY(orgId)) === 'true';
  } catch {
    return false;
  }
}

/**
 * Three things a new workspace owner does, in order, with the reason next to
 * each. Replaces the six-step wizard: the explanation sits beside the action.
 *
 * - connect: true once getConnectorsList(orgId) returns at least one connector
 * - verdict: true once the report has at least one passed or failed check
 * - report: the boss report, manual; marked done once the verdict exists and
 *   the user has visited /reports is not tracked, so it stays a link.
 */
export function FirstRunChecklist({ orgId, report, isDemo = false }: FirstRunChecklistProps) {
  const [hasConnector, setHasConnector] = useState<boolean | null>(null);
  const [dismissed, setDismissed] = useState(() => readDismissed(orgId));
  const [collapsed, setCollapsed] = useState(false);
  const [copied, setCopied] = useState<'idle' | 'done' | 'failed'>('idle');

  useEffect(() => {
    setDismissed(readDismissed(orgId));
  }, [orgId]);

  useEffect(() => {
    if (isDemo || !orgId) return;
    let cancelled = false;
    // Promise.resolve guards against a mocked or synchronous implementation.
    Promise.resolve()
      .then(() => getConnectorsList(orgId))
      .then((res) => {
        if (!cancelled) setHasConnector((res?.connectors?.length ?? 0) > 0);
      })
      .catch(() => {
        if (!cancelled) setHasConnector(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, isDemo]);

  if (isDemo || dismissed) return null;

  const checkCount = (report?.passed_checks?.length ?? 0) + (report?.failed_checks?.length ?? 0);
  const hasVerdict = checkCount > 0;

  const items: FirstRunItem[] = [
    { id: 'connect', ...FIRST_RUN_COPY.connect, done: hasConnector === true },
    { id: 'verdict', ...FIRST_RUN_COPY.verdict, done: hasVerdict },
    { id: 'report', ...FIRST_RUN_COPY.report, done: false },
  ];
  const doneCount = items.filter((i) => i.done).length;

  const handleDismiss = () => {
    try {
      localStorage.setItem(FIRST_RUN_DISMISSED_KEY(orgId), 'true');
    } catch {
      /* storage unavailable: hide for this visit only */
    }
    setDismissed(true);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(IT_HANDOFF_NOTE);
      setCopied('done');
    } catch {
      setCopied('failed');
    }
    window.setTimeout(() => setCopied('idle'), 2500);
  };

  return (
    <section
      className="bg-surface-container-low rounded-2xl border border-surface-bright m3-elevation-1"
      aria-labelledby="first-run-title"
      data-testid="first-run-checklist"
    >
      <div className="flex items-center justify-between gap-3 px-5 sm:px-6 py-4">
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          aria-expanded={!collapsed}
          aria-controls="first-run-items"
          className="flex items-center gap-3 text-left min-w-0"
        >
          <ChevronDown className={`w-4 h-4 text-on-surface-variant transition-transform shrink-0 ${collapsed ? '-rotate-90' : ''}`} aria-hidden="true" />
          <div className="min-w-0">
            <h2 id="first-run-title" className="text-base font-bold text-on-surface">
              First steps
            </h2>
            <p className="text-xs text-on-surface-variant" data-testid="first-run-progress">
              {doneCount} of {TOTAL} done
            </p>
          </div>
        </button>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Hide first steps"
          className="p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors shrink-0"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      {!collapsed && (
        <ol id="first-run-items" className="px-5 sm:px-6 pb-5 space-y-3">
          {items.map((item, index) => (
            <li
              key={item.id}
              className={`p-4 rounded-2xl border flex items-start gap-3 ${
                item.done ? 'border-ready-emerald/40 bg-ready-emerald/5' : 'border-outline-variant/40 bg-surface-container'
              }`}
              data-testid={`first-run-item-${item.id}`}
              data-done={item.done ? 'true' : 'false'}
            >
              <span
                className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0 mt-0.5 ${
                  item.done ? 'bg-ready-emerald text-slate-950' : 'bg-ready-emerald/15 text-ready-emerald'
                }`}
                aria-hidden="true"
              >
                {item.done ? <Check className="w-3.5 h-3.5" /> : index + 1}
              </span>
              <div className="min-w-0 flex-1">
                <Link
                  to={item.href}
                  className={`text-sm font-bold inline-flex items-center gap-1.5 hover:text-ready-emerald ${
                    item.done ? 'text-on-surface-variant line-through decoration-ready-emerald/60' : 'text-on-surface'
                  }`}
                >
                  {item.title}
                  {!item.done && <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />}
                </Link>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">{item.caption}</p>
                {item.id === 'connect' && !item.done && (
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
                    data-testid="copy-it-instructions"
                  >
                    <ClipboardCopy className="w-3.5 h-3.5" aria-hidden="true" />
                    {copied === 'done'
                      ? 'Copied. Paste it into an email to your IT person.'
                      : copied === 'failed'
                        ? 'Could not copy. Select the text on the Connected systems page instead.'
                        : "I'm not the admin. Copy instructions for my IT person"}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
