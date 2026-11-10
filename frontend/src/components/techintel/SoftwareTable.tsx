import React, { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, Search, PackageSearch } from 'lucide-react';
import type { StackItem, StackStatus, StackVulnerability } from '../../api';
import {
  Chip,
  ExploitedBadge,
  NotConfirmedChip,
  ReferenceLinks,
  SeverityChip,
  categoryLabel,
  formatDate,
  isExploited,
  isOnlyUnconfirmed,
  isUnconfirmed,
  newestSafeVersion,
  plural,
  severityRank,
  sortStackItems,
  statusCopy,
  timeAgo,
} from './shared';

type StatusFilter = 'all' | StackStatus;

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Everything' },
  { value: 'vulnerable', label: 'Needs an update' },
  { value: 'end_of_life', label: 'No longer supported' },
  { value: 'update_available', label: 'Newer version available' },
  { value: 'ok', label: 'Up to date' },
  { value: 'unknown', label: 'Not checked yet' },
];

const GRID = 'md:grid md:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)_minmax(0,1.6fr)_minmax(0,1.3fr)_minmax(0,1fr)_2rem] md:gap-4 md:items-center';

function matches(item: StackItem, query: string): boolean {
  if (!query) return true;
  const haystack = [
    item.name,
    item.vendor,
    item.version,
    item.asset,
    item.source,
    categoryLabel(item.category),
    ...(item.vulnerabilities || []).map(v => v.id),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every(term => haystack.includes(term));
}

function MobileLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="md:hidden text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mr-2">
      {children}
    </span>
  );
}

function VulnerabilityRow({ vuln }: { vuln: StackVulnerability }) {
  const published = formatDate(vuln.published);
  return (
    <li
      className={`rounded-lg border bg-surface-container p-3 space-y-2 ${
        vuln.known_exploited && !isUnconfirmed(vuln) ? 'border-critical-red/40' : 'border-outline-variant'
      }`}
      data-testid="vulnerability-row"
      data-confirmed={isUnconfirmed(vuln) ? 'false' : 'true'}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-mono font-bold text-on-surface">{vuln.id}</span>
        <SeverityChip severity={vuln.severity} cvss={vuln.cvss} />
        {isUnconfirmed(vuln) && <NotConfirmedChip />}
        {vuln.known_exploited && !isUnconfirmed(vuln) && <ExploitedBadge />}
        {published && <span className="text-[11px] text-on-surface-variant">Published {published}</span>}
      </div>
      <p className="text-sm text-on-surface leading-relaxed">{vuln.summary}</p>
      {isUnconfirmed(vuln) && (
        <p className="text-xs text-on-surface-variant leading-relaxed">
          Possible match: we could not verify that the exact version you run is affected. Ask IT to rule it out.
        </p>
      )}
      <p className="text-sm text-on-surface leading-relaxed">
        <strong>Fix:</strong>{' '}
        {vuln.fixed_version ? `upgrade to ${vuln.fixed_version}` : 'no fixed version has been published yet'}
        {vuln.remediation ? <span className="text-on-surface-variant">. {vuln.remediation}</span> : null}
      </p>
      <ReferenceLinks references={vuln.references} />
    </li>
  );
}

function EolInfo({ item }: { item: StackItem }) {
  const eol = item.eol;
  if (!eol) return null;
  const date = formatDate(eol.eol_date);
  let line: string;
  if (eol.is_eol) {
    line = date
      ? `The maker stopped releasing security fixes for this version on ${date}. New problems will not be repaired.`
      : 'The maker no longer releases security fixes for this version. New problems will not be repaired.';
  } else if (date) {
    line = `The maker releases security fixes for this version until ${date}.`;
  } else {
    line = 'This version still receives security fixes from the maker.';
  }
  return (
    <div
      className={`rounded-lg border bg-surface-container p-3 space-y-1 ${
        eol.is_eol ? 'border-drift-amber/40' : 'border-outline-variant'
      }`}
      data-testid="eol-info"
    >
      <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">Support from the maker</p>
      <p className="text-sm text-on-surface leading-relaxed">{line}</p>
      {eol.latest_version && (
        <p className="text-sm text-on-surface-variant">
          Newest release: <span className="font-mono font-semibold text-on-surface">{eol.latest_version}</span>
        </p>
      )}
      {eol.source && <p className="text-[11px] font-mono text-on-surface-variant/80">Source: {eol.source}</p>}
    </div>
  );
}

function ItemRow({ item }: { item: StackItem }) {
  const [open, setOpen] = useState(false);
  const onlyUnconfirmed = isOnlyUnconfirmed(item);
  const status = onlyUnconfirmed ? { label: 'Not confirmed', tone: 'unknown' as const } : statusCopy(item.status);
  const vulns = useMemo(
    () =>
      [...(item.vulnerabilities || [])].sort(
        (a, b) =>
          Number(isUnconfirmed(a)) - Number(isUnconfirmed(b)) ||
          Number(b.known_exploited) - Number(a.known_exploited) ||
          severityRank(a.severity) - severityRank(b.severity)
      ),
    [item.vulnerabilities]
  );
  const safe = newestSafeVersion(item);
  const exploited = isExploited(item);
  const seen = timeAgo(item.last_seen);
  const panelId = `stack-detail-${item.id}`;

  return (
    <li
      className={`rounded-xl border bg-surface-container-low ${exploited ? 'border-critical-red/40' : 'border-outline-variant'}`}
      data-testid="stack-row"
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`${item.name} ${item.version || ''}: ${status.label}. ${open ? 'Hide' : 'Show'} details`}
        className={`w-full text-left px-4 py-3.5 space-y-2 md:space-y-0 ${GRID} hover:bg-surface-container transition-colors rounded-xl cursor-pointer`}
      >
        <span className="flex items-start justify-between gap-3 md:block min-w-0">
          <span className="min-w-0">
            <span className="block text-sm font-bold text-on-surface break-words">{item.name}</span>
            <span className="block text-[11px] text-on-surface-variant">
              {[item.vendor, categoryLabel(item.category)].filter(Boolean).join(' · ')}
            </span>
          </span>
          <span className="md:hidden shrink-0 text-on-surface-variant">
            {open ? <ChevronUp className="w-4 h-4" aria-hidden="true" /> : <ChevronDown className="w-4 h-4" aria-hidden="true" />}
          </span>
        </span>

        <span className="block text-sm font-mono text-on-surface break-all">
          <MobileLabel>Version</MobileLabel>
          {item.version || 'Not known'}
        </span>

        <span className="block text-sm text-on-surface-variant break-words min-w-0">
          <MobileLabel>Where it runs</MobileLabel>
          {item.asset || 'Not tied to one system'}
        </span>

        <span className="flex flex-wrap items-center gap-1.5">
          <Chip tone={status.tone} testId="status-chip">{status.label}</Chip>
          {exploited && <ExploitedBadge />}
        </span>

        <span className="block text-sm font-mono text-on-surface break-all">
          <MobileLabel>Newest safe version</MobileLabel>
          {safe || <span className="font-sans text-on-surface-variant">Not known</span>}
        </span>

        <span className="hidden md:flex justify-end text-on-surface-variant">
          {open ? <ChevronUp className="w-4 h-4" aria-hidden="true" /> : <ChevronDown className="w-4 h-4" aria-hidden="true" />}
        </span>
      </button>

      {open && (
        <div id={panelId} className="px-4 pb-4 pt-1 border-t border-outline-variant space-y-3" data-testid="stack-detail">
          {vulns.length > 0 ? (
            <>
              <p className="pt-3 text-sm font-semibold text-on-surface">
                {onlyUnconfirmed
                  ? `${plural(vulns.length, 'possible security problem', 'possible security problems')} we could not confirm for this version`
                  : `${plural(vulns.length, 'known security problem', 'known security problems')} in this version`}
              </p>
              <ul className="space-y-2">
                {vulns.map(v => (
                  <VulnerabilityRow key={v.id} vuln={v} />
                ))}
              </ul>
            </>
          ) : (
            <p className="pt-3 text-sm text-on-surface-variant">
              {item.status === 'unknown'
                ? 'This program has not been checked against the security databases yet. Press "Check now" at the top of the page.'
                : 'No known security problems are published for this version.'}
            </p>
          )}
          <EolInfo item={item} />
          <p className="text-[11px] font-mono text-on-surface-variant/80">
            Found by: {item.source || 'not recorded'}
            {seen ? ` · last seen ${seen}` : ''}
          </p>
        </div>
      )}
    </li>
  );
}

interface SoftwareTableProps {
  items: StackItem[];
  /** Shown in the empty state when nothing has been found at all. */
  emptyAction?: React.ReactNode;
}

/**
 * Software and versions. One list that reads as a table on desktop and as
 * stacked cards on a phone. Default order puts what is being attacked first.
 */
export function SoftwareTable({ items, emptyAction }: SoftwareTableProps) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<StatusFilter>('all');

  const sorted = useMemo(() => sortStackItems(items || []), [items]);
  const counts = useMemo(() => {
    const c: Record<string, number> = { all: sorted.length };
    sorted.forEach(i => {
      c[i.status] = (c[i.status] || 0) + 1;
    });
    return c;
  }, [sorted]);
  const visible = useMemo(
    () => sorted.filter(i => (filter === 'all' || i.status === filter) && matches(i, query.trim())),
    [sorted, filter, query]
  );

  if (sorted.length === 0) {
    return (
      <div
        className="p-8 rounded-xl bg-surface-container-low border border-dashed border-outline-variant flex flex-col items-center text-center"
        data-testid="stack-empty"
      >
        <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
          <PackageSearch className="w-6 h-6" aria-hidden="true" />
        </div>
        <h3 className="text-base font-semibold text-on-surface">No software found yet</h3>
        <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
          We build this list from the systems you connect and the websites you add. Connect one, or add a program by
          hand, and it shows up here with its version and any known security problems.
        </p>
        {emptyAction && <div className="mt-4 flex flex-wrap items-center justify-center gap-3">{emptyAction}</div>}
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="software-table">
      <div className="flex flex-col lg:flex-row lg:items-center gap-3">
        <label className="relative flex-1 min-w-0">
          <span className="sr-only">Search software</span>
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by name, version, system or CVE number"
            className="w-full rounded-xl border border-outline-variant bg-surface-container-low pl-9 pr-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:outline-none focus:ring-2 focus:ring-ready-emerald/30"
            data-testid="stack-search"
          />
        </label>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
          {FILTERS.filter(f => f.value === 'all' || (counts[f.value] || 0) > 0).map(f => (
            <button
              key={f.value}
              type="button"
              onClick={() => setFilter(f.value)}
              aria-pressed={filter === f.value}
              className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors cursor-pointer ${
                filter === f.value
                  ? 'bg-ready-emerald/10 border-ready-emerald/40 text-ready-emerald'
                  : 'bg-surface-container-low border-outline-variant text-on-surface-variant hover:text-on-surface'
              }`}
              data-testid={`stack-filter-${f.value}`}
            >
              {f.label} <span className="font-mono font-normal opacity-80">{counts[f.value] || 0}</span>
            </button>
          ))}
        </div>
      </div>

      <div
        className={`hidden px-4 text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant ${GRID}`}
        aria-hidden="true"
      >
        <span>Software</span>
        <span>Version</span>
        <span>Where it runs</span>
        <span>Status</span>
        <span>Newest safe version</span>
        <span />
      </div>

      {visible.length === 0 ? (
        <p className="p-6 rounded-xl border border-dashed border-outline-variant text-center text-sm text-on-surface-variant" data-testid="stack-no-match">
          Nothing matches that search. Clear the search box or pick "Everything".
        </p>
      ) : (
        <ul className="space-y-2">
          {visible.map(item => (
            <ItemRow key={item.id} item={item} />
          ))}
        </ul>
      )}

      <p className="text-xs text-on-surface-variant" data-testid="stack-count">
        Showing {visible.length} of {plural(sorted.length, 'program', 'programs')}. Select a row to see what is wrong and how to fix it.
      </p>
    </div>
  );
}

export default SoftwareTable;
