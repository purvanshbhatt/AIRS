import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Wrench } from 'lucide-react';
import { getTechAdvisories } from '../../api';
import { deriveFixActions, type FixAction } from './shared';

/**
 * One line on the morning brief, pointing at Software Watch. Shown only when
 * there are confirmed items on the "Fix this week" list. Renders nothing
 * while loading, when there is nothing confirmed, or when the request fails.
 */
export function AdvisoryAlert({ orgId, className = '' }: { orgId?: string | null; className?: string }) {
  const [actions, setActions] = useState<FixAction[]>([]);

  useEffect(() => {
    let cancelled = false;
    setActions([]);
    if (!orgId) return;
    (async () => {
      try {
        const res = await getTechAdvisories(orgId);
        const list = deriveFixActions({
          topActions: Array.isArray(res?.top_actions) ? res.top_actions : null,
          advisories: Array.isArray(res?.advisories) ? res.advisories : [],
        });
        if (!cancelled) setActions(list);
      } catch {
        /* silent: this line is a bonus, never an error on the brief */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [orgId]);

  if (actions.length === 0) return null;

  return (
    <Link
      to="/technology/intelligence"
      className={`group flex items-center gap-2 rounded-xl border border-drift-amber/40 bg-drift-amber/10 px-4 py-2.5 text-sm text-on-surface hover:bg-drift-amber/15 transition-colors ${className}`}
      data-testid="advisory-alert"
    >
      <Wrench className="w-4 h-4 text-drift-amber shrink-0" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">
        <strong>
          {actions.length} {actions.length === 1 ? 'thing' : 'things'} to fix this week:
        </strong>{' '}
        {actions[0].title}
      </span>
      <ArrowRight className="w-4 h-4 text-on-surface-variant shrink-0 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
    </Link>
  );
}

export default AdvisoryAlert;
