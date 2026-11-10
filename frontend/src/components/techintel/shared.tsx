import React from 'react';
import { Flame, ExternalLink } from 'lucide-react';
import type {
  StackCategory,
  StackItem,
  StackStatus,
  TechAdvisory,
  TechCoverage,
  TechIssue,
  TechTopAction,
} from '../../api';

/**
 * Shared pieces for the Software Watch page.
 *
 * Everything here is derived from API fields. No count, version or date is
 * invented: when the backend does not send a value the copy says so.
 */

export type Tone = 'ready' | 'warning' | 'critical' | 'unknown';

export const toneText: Record<Tone, string> = {
  ready: 'text-ready-emerald',
  warning: 'text-drift-amber',
  critical: 'text-critical-red',
  unknown: 'text-on-surface-variant',
};

export const toneBorder: Record<Tone, string> = {
  ready: 'border-ready-emerald/40',
  warning: 'border-drift-amber/40',
  critical: 'border-critical-red/40',
  unknown: 'border-outline-variant',
};

const chipBase =
  'inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-semibold whitespace-nowrap';

export const toneChip: Record<Tone, string> = {
  ready: 'bg-ready-emerald/10 border-ready-emerald/30 text-ready-emerald',
  warning: 'bg-drift-amber/10 border-drift-amber/30 text-drift-amber',
  critical: 'bg-critical-red/10 border-critical-red/30 text-critical-red',
  unknown: 'bg-surface-container border-outline-variant text-on-surface-variant',
};

export function Chip({
  tone = 'unknown',
  children,
  className = '',
  title,
  testId,
}: {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
  title?: string;
  testId?: string;
}) {
  return (
    <span className={`${chipBase} ${toneChip[tone]} ${className}`} title={title} data-testid={testId}>
      {children}
    </span>
  );
}

/* ------------------------------------------------------------------------- */
/* Wording                                                                    */
/* ------------------------------------------------------------------------- */

export const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

const SEVERITY_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, unknown: 4 };

export const severityRank = (s?: string | null) => SEVERITY_RANK[String(s || 'unknown').toLowerCase()] ?? 4;

export const severityTone = (s?: string | null): Tone => {
  const v = String(s || '').toLowerCase();
  if (v === 'critical') return 'critical';
  if (v === 'high' || v === 'medium') return 'warning';
  return 'unknown';
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  unknown: 'Not rated',
};

export const severityLabel = (s?: string | null) => SEVERITY_LABEL[String(s || 'unknown').toLowerCase()] || 'Not rated';

export function SeverityChip({ severity, cvss }: { severity?: string | null; cvss?: number | null }) {
  return (
    <Chip tone={severityTone(severity)} title={typeof cvss === 'number' ? `CVSS ${cvss}` : undefined}>
      {severityLabel(severity)}
      {typeof cvss === 'number' && <span className="font-mono font-normal opacity-80">{cvss.toFixed(1)}</span>}
    </Chip>
  );
}

export function ExploitedBadge() {
  return (
    <Chip tone="critical" testId="exploited-badge" title="Listed as actively exploited (CISA Known Exploited Vulnerabilities)">
      <Flame className="w-3 h-3" aria-hidden="true" />
      Being exploited now
    </Chip>
  );
}

export const STATUS_COPY: Record<StackStatus, { label: string; tone: Tone }> = {
  vulnerable: { label: 'Needs an update', tone: 'critical' },
  end_of_life: { label: 'No longer supported', tone: 'warning' },
  update_available: { label: 'Newer version available', tone: 'warning' },
  ok: { label: 'Up to date', tone: 'ready' },
  unknown: { label: 'Not checked yet', tone: 'unknown' },
};

export const statusCopy = (status?: string | null) =>
  STATUS_COPY[(status || 'unknown') as StackStatus] || STATUS_COPY.unknown;

export const CATEGORY_LABEL: Record<StackCategory, string> = {
  os: 'Operating system',
  runtime: 'Programming runtime',
  database: 'Database',
  web_server: 'Web server',
  framework: 'App framework',
  application: 'Application',
  cloud_service: 'Cloud service',
  library: 'Code library',
};

export const categoryLabel = (c?: string | null) =>
  CATEGORY_LABEL[(c || '') as StackCategory] || titleCase(String(c || 'Other'));

export function titleCase(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .trim()
    .replace(/\b\w/g, m => m.toUpperCase());
}

/* ------------------------------------------------------------------------- */
/* Dates                                                                      */
/* ------------------------------------------------------------------------- */

export function parseDate(value?: string | null): Date | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatDate(value?: string | null): string | null {
  const d = parseDate(value);
  if (!d) return null;
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function formatDateTime(value?: string | null): string | null {
  const d = parseDate(value);
  if (!d) return null;
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

/** "5 minutes ago", "3 hours ago", "2 days ago"; falls back to the date. */
export function timeAgo(value?: string | null, now: Date = new Date()): string | null {
  const d = parseDate(value);
  if (!d) return null;
  const mins = Math.round((now.getTime() - d.getTime()) / 60000);
  if (mins < 0) return formatDateTime(value);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${plural(mins, 'minute', 'minutes')} ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${plural(hours, 'hour', 'hours')} ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${plural(days, 'day', 'days')} ago`;
  return formatDate(value);
}

/* ------------------------------------------------------------------------- */
/* Stack helpers                                                              */
/* ------------------------------------------------------------------------- */

/* ------------------------------------------------------------------------- */
/* Confidence                                                                 */
/* ------------------------------------------------------------------------- */

type WithConfidence = { confidence?: string | null } | null | undefined;

/** The backend classified the match and it is not a proven one. */
export const isUnconfirmed = (x: WithConfidence) =>
  x?.confidence != null && String(x.confidence).toLowerCase() !== 'confirmed';

/** Lenient: used for ordering and labels inside "Everything we checked". */
export const isConfirmed = (x: WithConfidence) => !isUnconfirmed(x);

/**
 * Strict: only an explicit "confirmed" from the backend counts. An item the
 * backend did not classify never reaches the "Fix this week" list.
 */
export const isProven = (x: WithConfidence) => String(x?.confidence ?? '').toLowerCase() === 'confirmed';

export function NotConfirmedChip() {
  return (
    <Chip
      testId="not-confirmed-chip"
      title="A possible match we could not verify against the exact version you run. It is listed so IT can rule it out."
    >
      Not confirmed
    </Chip>
  );
}

/** A program flagged as vulnerable only by matches that were not verified. */
export const isOnlyUnconfirmed = (item: StackItem) => {
  const vulns = item.vulnerabilities || [];
  return item.status === 'vulnerable' && vulns.length > 0 && vulns.every(isUnconfirmed);
};

export const isExploited = (item: StackItem) =>
  (item.vulnerabilities || []).some(v => v.known_exploited && isConfirmed(v));

const STATUS_RANK: Record<string, number> = {
  vulnerable: 0,
  end_of_life: 1,
  update_available: 2,
  unknown: 3,
  ok: 4,
};

const worstSeverity = (item: StackItem) =>
  (item.vulnerabilities || []).reduce((worst, v) => Math.min(worst, severityRank(v.severity)), 4);

/** Default order: being exploited now, then vulnerable (worst first), then the rest. */
export function sortStackItems(items: StackItem[]): StackItem[] {
  return [...items].sort((a, b) => {
    const ex = Number(isExploited(b)) - Number(isExploited(a));
    if (ex !== 0) return ex;
    const st = (STATUS_RANK[a.status] ?? 3) - (STATUS_RANK[b.status] ?? 3);
    if (st !== 0) return st;
    const conf = Number(isOnlyUnconfirmed(a)) - Number(isOnlyUnconfirmed(b));
    if (conf !== 0) return conf;
    const sev = worstSeverity(a) - worstSeverity(b);
    if (sev !== 0) return sev;
    return String(a.name || '').localeCompare(String(b.name || ''));
  });
}

/** Numeric-aware version comparison ("1.10.0" > "1.9.3"). */
export function compareVersions(a: string, b: string): number {
  const pa = String(a).split(/[.\-+_]/);
  const pb = String(b).split(/[.\-+_]/);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const x = pa[i] ?? '0';
    const y = pb[i] ?? '0';
    const nx = Number.parseInt(x, 10);
    const ny = Number.parseInt(y, 10);
    if (!Number.isNaN(nx) && !Number.isNaN(ny)) {
      if (nx !== ny) return nx - ny;
    } else if (x !== y) {
      return x.localeCompare(y);
    }
  }
  return 0;
}

/**
 * The version to move to. Uses the newest release when the backend knows it,
 * otherwise the highest version that fixes every listed problem.
 * Returns null when the backend sent neither.
 */
export function newestSafeVersion(item: StackItem): string | null {
  const fixes = (item.vulnerabilities || [])
    .map(v => v.fixed_version)
    .filter((v): v is string => Boolean(v));
  const highestFix = fixes.length ? fixes.reduce((hi, v) => (compareVersions(v, hi) > 0 ? v : hi)) : null;
  const latest = item.eol?.latest_version || null;
  if (latest && highestFix) return compareVersions(highestFix, latest) > 0 ? highestFix : latest;
  return latest || highestFix;
}

/* ------------------------------------------------------------------------- */
/* Advisories                                                                 */
/* ------------------------------------------------------------------------- */

export const isUrgentAdvisory = (a: Pick<TechAdvisory, 'severity' | 'known_exploited' | 'confidence'>) =>
  isConfirmed(a) && (Boolean(a?.known_exploited) || String(a?.severity || '').toLowerCase() === 'critical');

/* ------------------------------------------------------------------------- */
/* URLs                                                                       */
/* ------------------------------------------------------------------------- */

/** Only http(s) links from API data are rendered as links. */
export function safeHttpUrl(value?: string | null): string | null {
  if (!value) return null;
  try {
    const u = new URL(String(value).trim());
    return u.protocol === 'http:' || u.protocol === 'https:' ? u.toString() : null;
  } catch {
    return null;
  }
}

export function hostOf(value: string): string {
  try {
    return new URL(value).hostname.replace(/^www\./, '');
  } catch {
    return value;
  }
}

export const WEB_URL_ERROR =
  'Enter a web address that starts with https:// or http://, for example https://www.yourpractice.com';

/**
 * Validates a website address typed by a person. A bare domain
 * ("yourpractice.com") is accepted and treated as https. Anything that is
 * not http or https is rejected.
 */
export function normalizeWebUrl(input: string): { url: string } | { error: string } {
  const raw = String(input || '').trim();
  if (!raw) return { error: 'Enter the web address you want checked.' };
  if (/\s/.test(raw)) return { error: WEB_URL_ERROR };
  const hasScheme = /^[a-z][a-z0-9+.-]*:/i.test(raw) && !/^[^/:]+:\d+(\/|$)/.test(raw);
  const candidate = hasScheme ? raw : `https://${raw}`;
  try {
    const u = new URL(candidate);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return { error: WEB_URL_ERROR };
    if (u.username || u.password) return { error: 'Remove the user name and password from the address.' };
    const host = u.hostname;
    if (!host || (!host.includes('.') && host !== 'localhost')) return { error: WEB_URL_ERROR };
    return { url: u.toString() };
  } catch {
    return { error: WEB_URL_ERROR };
  }
}

export function ReferenceLinks({ references, className = '' }: { references?: string[] | null; className?: string }) {
  const links = (references || []).map(safeHttpUrl).filter((u): u is string => Boolean(u));
  if (links.length === 0) return null;
  return (
    <ul className={`flex flex-wrap gap-x-4 gap-y-1 text-xs ${className}`} data-testid="reference-links">
      {links.map(url => (
        <li key={url}>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-ready-emerald hover:underline break-all"
          >
            {hostOf(url)}
            <ExternalLink className="w-3 h-3 shrink-0" aria-hidden="true" />
          </a>
        </li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------------- */
/* Issues (shared by websites and cloud services)                             */
/* ------------------------------------------------------------------------- */

export function IssueList({ issues, testId = 'issue-list' }: { issues?: TechIssue[] | null; testId?: string }) {
  const list = [...(issues || [])].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
  if (list.length === 0) return null;
  return (
    <ul className="space-y-2" data-testid={testId}>
      {list.map((issue, i) => (
        <li
          key={`${issue.title}-${i}`}
          className={`rounded-lg border bg-surface-container p-3 ${toneBorder[severityTone(issue.severity)]}`}
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-on-surface">{issue.title}</span>
            <SeverityChip severity={issue.severity} />
            {isUnconfirmed(issue) && <NotConfirmedChip />}
          </div>
          {issue.fix && (
            <p className="mt-1 text-xs text-on-surface-variant leading-relaxed">
              <strong className="text-on-surface">Fix:</strong> {issue.fix}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------------- */
/* Source chips                                                               */
/* ------------------------------------------------------------------------- */

export function sourceTone(value: string): Tone {
  const v = String(value || '').toLowerCase();
  if (/error|fail|denied|invalid|expired|unreachable/.test(v)) return 'critical';
  if (/not[ _-]?(connected|configured|available)|missing|disabled|none|unknown|pending|stale|demo|example/.test(v)) return 'unknown';
  if (/connected|ok|live|active|healthy|fresh|ready|success/.test(v)) return 'ready';
  return 'unknown';
}

export function SourceChips({
  sources,
  label = 'Where this comes from',
  testId = 'source-chips',
}: {
  sources?: Record<string, string> | null;
  label?: string;
  testId?: string;
}) {
  const entries = Object.entries(sources || {});
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2" data-testid={testId}>
      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">{label}</span>
      {entries.map(([name, state]) => (
        <Chip key={name} tone={sourceTone(state)}>
          <span className="font-mono uppercase">{name.replace(/_/g, ' ')}</span>
          <span className="font-normal">{String(state).replace(/_/g, ' ')}</span>
        </Chip>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------------- */
/* Errors                                                                     */
/* ------------------------------------------------------------------------- */

export const errorStatus = (err: unknown): number | undefined =>
  typeof (err as { status?: unknown })?.status === 'number' ? (err as { status: number }).status : undefined;

/** Plain words for a failed request. The raw message is kept for IT as `detail`. */
export function plainError(err: unknown, action: string): { message: string; detail?: string } {
  const status = errorStatus(err);
  const detail = err instanceof Error && err.message ? err.message : undefined;
  if (status === 401) return { message: 'Your session ended. Sign in again, then retry.', detail };
  if (status === 403) {
    if (detail && /read-only demo/i.test(detail)) {
      return { message: 'This is the example workspace, so changes and live checks are switched off here.' };
    }
    return { message: `Your account is not allowed to ${action}. Ask the workspace owner for access.`, detail };
  }
  if (status === 404) return { message: `We could not ${action} because this workspace has nothing set up for it yet.`, detail };
  if (status === 429) return { message: 'Too many checks in a short time. Wait a minute, then try again.', detail };
  if (status && status >= 500) return { message: `We could not ${action} right now. The service had a problem. Try again in a few minutes.`, detail };
  if (!status) return { message: `We could not ${action}. Check your internet connection and try again.`, detail };
  return { message: `We could not ${action}. Try again in a few minutes.`, detail };
}

/* ------------------------------------------------------------------------- */
/* "Fix this week"                                                            */
/* ------------------------------------------------------------------------- */

export const MAX_FIX_ACTIONS = 5;

/** One card of the short action list, already in display form. */
export interface FixAction {
  id: string;
  /** Plain-English headline. Never contains a CVE number. */
  title: string;
  /** Where it is: system or program names. */
  names: string[];
  count: number;
  /** The one step to take. */
  fixStep: string;
  /** Ready-to-paste message for the IT person. */
  sendText: string;
  sourceUrl: string | null;
  /** Advisory number (CVE and similar). Shown as small secondary text only. */
  reference: string | null;
  exploited: boolean;
  endOfLife: boolean;
}

const ADVISORY_ID = /\b(?:CVE-\d{4}-\d{3,}|GHSA(?:-[0-9a-z]{4}){3})\b/gi;

const uniq = (values: string[]) => Array.from(new Set(values.map(v => String(v).trim()).filter(Boolean)));

function toNames(value: unknown): string[] {
  if (!value) return [];
  if (typeof value === 'string') return uniq(value.split(/\s*[,;]\s*/));
  if (Array.isArray(value)) {
    return uniq(
      value.map(v => {
        if (typeof v === 'string') return v;
        if (v && typeof v === 'object') {
          const o = v as Record<string, unknown>;
          return String(o.asset || o.label || [o.name, o.version].filter(Boolean).join(' ') || '');
        }
        return '';
      })
    );
  }
  if (typeof value === 'object') {
    // Backend `where` block: { count, label, names }.
    const o = value as Record<string, unknown>;
    if (Array.isArray(o.names)) return toNames(o.names);
    if (typeof o.label === 'string') return [o.label];
  }
  return [];
}

/** Headlines are for a non-technical reader: advisory numbers are moved out of them. */
function plainTitle(raw: string, names: string[]): string {
  const cleaned = String(raw || '')
    .replace(ADVISORY_ID, '')
    .replace(/\(\s*\)|\[\s*\]/g, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/^[\s:;,.–-]+|[\s:;,–-]+$/g, '')
    .trim();
  if (cleaned) return cleaned;
  return names.length ? `A security update is needed for ${names[0]}` : 'A security update is needed';
}

function firstSafeUrl(...candidates: unknown[]): string | null {
  for (const c of candidates.flat()) {
    const url = safeHttpUrl(typeof c === 'string' ? c : null);
    if (url) return url;
  }
  return null;
}

export function whereText(action: Pick<FixAction, 'names' | 'count'>): string {
  const shown = action.names.slice(0, 4);
  const more = Math.max(action.count, action.names.length) - shown.length;
  if (shown.length === 0) {
    return action.count > 0 ? `Found in ${plural(action.count, 'place', 'places')}` : 'Location not reported';
  }
  const count = Math.max(action.count, action.names.length);
  return `Found in ${plural(count, 'place', 'places')}: ${shown.join(', ')}${more > 0 ? ` and ${more} more` : ''}`;
}

function generatedSendText(a: Omit<FixAction, 'sendText'>): string {
  return [
    `Hi, our security check flagged something to fix this week: ${a.title.replace(/[.\s]+$/, '')}.`,
    `${whereText(a)}.`,
    `What to do: ${a.fixStep.replace(/[.\s]+$/, '')}.`,
    a.reference ? `Reference: ${a.reference}.` : '',
    a.sourceUrl ? `Details: ${a.sourceUrl}` : '',
    'Please let me know when it is done.',
  ]
    .filter(Boolean)
    .join(' ');
}

function finish(a: Omit<FixAction, 'sendText'>, sendToItText?: unknown): FixAction {
  const provided = typeof sendToItText === 'string' ? sendToItText.trim() : '';
  return { ...a, sendText: provided || generatedSendText(a) };
}

type RawAction = TechTopAction & TechAdvisory & Record<string, unknown>;

function toFixAction(input: TechTopAction | TechAdvisory, index: number): FixAction {
  const raw = input as RawAction;
  const names = toNames(raw.where).length
    ? toNames(raw.where)
    : toNames(raw.affected).length
      ? toNames(raw.affected)
      : toNames(raw.systems || raw.assets);
  const ids = [raw.cve_id, ...(Array.isArray(raw.cve_ids) ? raw.cve_ids : []), raw.id].filter(
    (v): v is string => typeof v === 'string' && v.length > 0
  );
  const reference = ids.find(v => new RegExp(ADVISORY_ID.source, 'i').test(v)) || null;
  const steps = Array.isArray(raw.steps) ? raw.steps.filter(Boolean) : [];
  // One step only. A stated fix wins; then the version that repairs it; then the first listed step.
  const programs = uniq((Array.isArray(raw.affected) ? raw.affected : []).map(a => String(a?.name || '')));
  const upgrade = raw.fixed_version
    ? `Upgrade ${programs.length === 1 ? `${programs[0]} ` : ''}to version ${raw.fixed_version} or newer.`
    : null;
  const fixStep =
    [raw.fix_step, raw.fix, upgrade, steps[0]].find((v): v is string => typeof v === 'string' && v.trim().length > 0) ||
    "Ask IT to follow the maker's guidance in the source link.";
  const eol = raw.eol as { is_eol?: boolean } | boolean | undefined;
  const whereBlock = raw.where && typeof raw.where === 'object' && !Array.isArray(raw.where)
    ? (raw.where as { count?: unknown })
    : null;
  const statedCount = [raw.count, whereBlock?.count].find((v): v is number => typeof v === 'number' && v > 0);
  const kind = String(raw.kind || '').toLowerCase();
  return finish(
    {
      id: String(raw.id || raw.cve_id || raw.title || raw.summary || `action-${index}`),
      title: plainTitle(String(raw.title || raw.summary || ''), names),
      names,
      count: statedCount ?? names.length,
      fixStep: fixStep.trim(),
      sourceUrl: firstSafeUrl(raw.source_url, raw.source_link, raw.url, raw.references || []),
      reference,
      exploited: Boolean(raw.known_exploited) || kind === 'known_exploited',
      endOfLife:
        kind === 'end_of_life' ||
        Boolean(raw.end_of_life || raw.is_eol || eol === true || (eol && typeof eol === 'object' && eol.is_eol)),
    },
    raw.send_to_it_text
  );
}

/** End-of-life programs become one card per program and version, listing every system that runs it. */
function eolActions(items: StackItem[]): FixAction[] {
  const groups = new Map<string, StackItem[]>();
  items
    .filter(i => (i.status === 'end_of_life' || i.eol?.is_eol) && isProven(i as WithConfidence))
    .forEach(i => {
      const key = `${i.name}@${i.version}`;
      groups.set(key, [...(groups.get(key) || []), i]);
    });
  return Array.from(groups.entries()).map(([key, group]) => {
    const first = group[0];
    const label = [first.name, first.version].filter(Boolean).join(' ');
    const names = uniq(group.map(i => i.asset || '')).length ? uniq(group.map(i => i.asset || '')) : [label];
    const latest = first.eol?.latest_version;
    return finish({
      id: `eol:${key}`,
      title: `${label} no longer gets security fixes from its maker`,
      names,
      count: Math.max(names.length, group.length),
      fixStep: latest
        ? `Move to ${first.name} ${latest}, or another version the maker still supports.`
        : `Move ${first.name} to a version the maker still supports.`,
      sourceUrl: firstSafeUrl(first.eol?.source),
      reference: null,
      exploited: false,
      endOfLife: true,
    });
  });
}

/**
 * The short list at the top of the page: at most five confirmed items.
 * Uses the backend's `top_actions` when it sends them. Otherwise it is built
 * from advisories that are being exploited or flagged end-of-life, plus
 * programs the maker no longer supports.
 */
export function deriveFixActions(input: {
  topActions?: TechTopAction[] | null;
  advisories?: TechAdvisory[] | null;
  items?: StackItem[] | null;
}): FixAction[] {
  let actions: FixAction[];
  if (Array.isArray(input.topActions)) {
    actions = input.topActions.filter(a => a && isProven(a)).map(toFixAction);
  } else {
    const fromAdvisories = (input.advisories || [])
      .filter(
        a =>
          a &&
          isProven(a) &&
          (a.known_exploited || a.end_of_life || (a as { kind?: string }).kind === 'end_of_life')
      )
      .map(toFixAction);
    actions = [...fromAdvisories, ...eolActions(input.items || [])].sort(
      (a, b) => Number(b.exploited) - Number(a.exploited)
    );
  }
  const seen = new Set<string>();
  return actions
    .filter(a => (seen.has(a.id) ? false : (seen.add(a.id), true)))
    .slice(0, MAX_FIX_ACTIONS);
}

/* ------------------------------------------------------------------------- */
/* Coverage                                                                   */
/* ------------------------------------------------------------------------- */

export interface CoverageView {
  checked: string[];
  unseen: string[];
}

/** Backend source ids in words a non-technical reader knows. */
const SOURCE_LABELS: Record<string, string> = {
  aws: 'servers in AWS',
  microsoft: 'computers managed in Microsoft 365',
  ms_graph: 'computers managed in Microsoft 365',
  wazuh: 'computers with the Wazuh agent',
  web_scan: 'your website',
  application_manifest: 'software your apps declare',
  manual: 'software you added by hand',
  registry: 'software you added by hand',
};

const sourceLabel = (name: string) => {
  const known = SOURCE_LABELS[String(name).toLowerCase().trim()];
  if (known) return known;
  const clean = String(name).replace(/[_-]+/g, ' ').trim();
  return clean.length <= 4 ? clean.toUpperCase() : titleCase(clean);
};

const CHECKED_KEYS = ['sources_seen', 'checked', 'sources_checked', 'covered', 'visible'];
const UNSEEN_KEYS = ['not_seen', 'could_not_see', 'not_visible', 'not_checked', 'not_covered', 'missing', 'unseen', 'gaps'];

/**
 * What we looked at and what we could not. Reads the backend's `coverage`
 * block; when that is absent, falls back to the per-source status map
 * (a connected source was checked, anything else could not be seen).
 */
export function deriveCoverage(
  coverage?: TechCoverage | null,
  ...sourceMaps: (Record<string, string> | null | undefined)[]
): CoverageView {
  if (coverage && typeof coverage === 'object') {
    const pick = (keys: string[]) => uniq(keys.flatMap(k => toNames((coverage as Record<string, unknown>)[k])));
    // Source ids become plain words; sentences the backend wrote pass through.
    const checked = uniq(pick(CHECKED_KEYS).map(n => (/\s/.test(n) ? n : sourceLabel(n))));
    const unseen = pick(UNSEEN_KEYS).filter(n => !checked.includes(n));
    if (checked.length || unseen.length) return { checked, unseen };
  }
  const checked: string[] = [];
  const unseen: string[] = [];
  sourceMaps.forEach(map =>
    Object.entries(map || {}).forEach(([name, state]) => {
      (sourceTone(state) === 'ready' ? checked : unseen).push(sourceLabel(name));
    })
  );
  const c = uniq(checked);
  return { checked: c, unseen: uniq(unseen).filter(n => !c.includes(n)) };
}

export function coverageText(view: CoverageView): { checked: string; unseen: string } {
  return {
    checked: `We checked: ${view.checked.length ? view.checked.join(', ') : 'nothing yet'}.`,
    unseen: `We could not see: ${view.unseen.length ? view.unseen.join(', ') : 'anything that is not connected'}.`,
  };
}

/**
 * When the advisory feeds were last read: the oldest `as_of` across feeds that
 * were used, so the page never claims to be fresher than its stalest source.
 */
export function feedsAsOf(feeds?: Record<string, { as_of?: string | null; status?: string } | null> | null): string | null {
  const times = Object.values(feeds || {})
    .filter(f => f && f.status !== 'not_used' && f.as_of)
    .map(f => String(f!.as_of))
    .filter(t => !Number.isNaN(Date.parse(t)))
    .sort((a, b) => Date.parse(a) - Date.parse(b));
  return times[0] || null;
}
