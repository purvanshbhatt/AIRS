import React from 'react';
import { ShieldCheck, UserCog, Clock } from 'lucide-react';
import type { TechAdvisory } from '../../api';
import {
  ExploitedBadge,
  NotConfirmedChip,
  ReferenceLinks,
  SeverityChip,
  formatDate,
  isUnconfirmed,
  isUrgentAdvisory,
  severityTone,
  timeAgo,
  toneBorder,
} from './shared';

function whoAndWhen(advisory: TechAdvisory): { who: string; when: string } {
  const sev = String(advisory.severity || '').toLowerCase();
  if (advisory.known_exploited) {
    return {
      who: 'Your IT provider (MSP). Forward this card to them and ask for a confirmation when it is done.',
      when: 'Today. Attackers are already using this.',
    };
  }
  if (sev === 'critical') {
    return {
      who: 'Your IT provider (MSP). Forward this card to them and ask for a confirmation when it is done.',
      when: 'This week, sooner if the system is reachable from the internet.',
    };
  }
  if (sev === 'high') {
    return { who: 'Your IT provider (MSP).', when: 'At the next scheduled maintenance, within the month.' };
  }
  return { who: 'Your IT provider (MSP).', when: 'At a routine IT visit.' };
}

function AdvisoryCard({ advisory }: { advisory: TechAdvisory }) {
  const urgent = isUrgentAdvisory(advisory);
  const unconfirmed = isUnconfirmed(advisory);
  const tone = unconfirmed ? 'unknown' : urgent ? 'critical' : severityTone(advisory.severity);
  const { who, when } = whoAndWhen(advisory);
  const published = formatDate(advisory.published);
  const affected = advisory.affected || [];
  const steps = advisory.steps || [];

  return (
    <li
      className={`rounded-2xl border border-l-4 bg-surface-container-low p-5 space-y-4 ${toneBorder[tone]}`}
      data-testid="advisory-card"
      data-urgent={urgent ? 'true' : 'false'}
      data-confirmed={unconfirmed ? 'false' : 'true'}
    >
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityChip severity={advisory.severity} cvss={advisory.cvss} />
          {unconfirmed && <NotConfirmedChip />}
          {advisory.known_exploited && !unconfirmed && <ExploitedBadge />}
          <span className="text-[11px] font-mono text-on-surface-variant">{advisory.id}</span>
          {published && <span className="text-[11px] text-on-surface-variant">Published {published}</span>}
        </div>
        <h3 className="text-base font-bold text-on-surface leading-snug">{advisory.summary}</h3>
        {unconfirmed && (
          <p className="text-xs text-on-surface-variant leading-relaxed">
            Possible match: we could not verify that the exact version you run is affected. Ask IT to rule it out
            before spending time on it.
          </p>
        )}
      </div>

      <div>
        <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mb-1.5">
          Who is affected
        </p>
        {affected.length === 0 ? (
          <p className="text-sm text-on-surface-variant">The affected systems were not listed.</p>
        ) : (
          <ul className="space-y-1 text-sm text-on-surface" data-testid="advisory-affected">
            {affected.map((a, i) => (
              <li key={`${a.name}-${a.asset}-${i}`}>
                <span className="font-semibold">{a.name}</span>
                {a.version && <span className="font-mono text-on-surface-variant"> {a.version}</span>}
                <span className="text-on-surface-variant">{a.asset ? ` on ${a.asset}` : ' (system not identified)'}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mb-1.5">
          What to do
        </p>
        {steps.length > 0 ? (
          <ol className="list-decimal pl-5 space-y-1.5 text-sm text-on-surface leading-relaxed" data-testid="advisory-steps">
            {steps.map((step, i) => (
              <li key={`${i}-${step}`}>{step}</li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-on-surface">
            {advisory.fixed_version
              ? `Upgrade the affected software to version ${advisory.fixed_version} or newer.`
              : 'No fixed version has been published yet. Ask IT to follow the maker\'s guidance in the links below.'}
          </p>
        )}
        {advisory.fixed_version && steps.length > 0 && (
          <p className="mt-2 text-xs text-on-surface-variant">
            Fixed in version <span className="font-mono font-semibold text-on-surface">{advisory.fixed_version}</span>
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-outline-variant">
          <UserCog className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
          <span className="text-on-surface-variant">
            <strong className="text-on-surface block">Who should do it</strong>
            {who}
          </span>
        </div>
        <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-outline-variant">
          <Clock className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
          <span className="text-on-surface-variant">
            <strong className="text-on-surface block">How soon</strong>
            {when}
          </span>
        </div>
      </div>

      <ReferenceLinks references={advisory.references} />
    </li>
  );
}

interface AdvisoriesListProps {
  advisories: TechAdvisory[];
  generatedAt?: string | null;
  /** True when the software list itself is empty, so "nothing to fix" would be misleading. */
  nothingTracked?: boolean;
}

/** Every finding, inside "Everything we checked": urgent first, unconfirmed matches last and labelled. */
export function AdvisoriesList({ advisories, generatedAt, nothingTracked = false }: AdvisoriesListProps) {
  const returned = advisories || [];
  // Backend order is kept inside each group: urgent and confirmed first, unconfirmed matches last.
  const list = [
    ...returned.filter(isUrgentAdvisory),
    ...returned.filter(a => !isUrgentAdvisory(a) && !isUnconfirmed(a)),
    ...returned.filter(isUnconfirmed),
  ];
  const hasUnconfirmed = returned.some(isUnconfirmed);
  const generated = timeAgo(generatedAt);

  if (list.length === 0) {
    return (
      <div
        className="p-8 rounded-xl bg-surface-container-low border border-dashed border-outline-variant flex flex-col items-center text-center"
        data-testid="advisories-empty"
      >
        <div className="w-12 h-12 rounded-2xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald mb-3">
          <ShieldCheck className="w-6 h-6" aria-hidden="true" />
        </div>
        <h3 className="text-base font-semibold text-on-surface">
          {nothingTracked ? 'Nothing to check yet' : 'Nothing to fix right now'}
        </h3>
        <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
          {nothingTracked
            ? 'Once we can see your software, any update you need to make is listed here with step-by-step instructions for IT.'
            : 'No published security problem matches the software versions we can see. Press "Check now" to look again.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="advisories-list">
      <p className="text-sm text-on-surface-variant" data-testid="advisories-summary">
        Every published problem that matches the software we can see, most urgent first.
        {hasUnconfirmed ? ' Items marked "Not confirmed" are possible matches we could not verify.' : ''}
        {generated ? ` List built ${generated}.` : ''}
      </p>
      <ol className="space-y-4 list-none p-0">
        {list.map(a => (
          <AdvisoryCard key={a.id} advisory={a} />
        ))}
      </ol>
    </div>
  );
}

export default AdvisoriesList;
