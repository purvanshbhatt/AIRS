import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Plug, RotateCcw } from 'lucide-react';
import { getDailyReadinessReport } from '../../api';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { LoadingState, ErrorState } from '../readiness/ReadinessStates';
import { ConnectFirstEmptyState } from '../readiness/PlainLanguage';

/**
 * The live view of a technology area (identity, devices, backups, email,
 * cloud, AI) for a real organisation.
 *
 * Everything shown here is read from the organisation's own readiness report
 * (`GET /api/clinic/readiness/{org_id}`): the checks that report produced and
 * the systems that are connected. Nothing is illustrative. When no connected
 * system reports on the area, the page says so instead of showing numbers.
 *
 * The sample walkthrough of each area (see `pages/technology/*Page.tsx`) is
 * shown only in the demo workspace, under its "Simulated Telemetry" banner.
 */

export type DomainKey = 'identity' | 'devices' | 'backups' | 'email' | 'cloud' | 'ai';

interface DomainConfig {
  title: string;
  /** How the area is named inside a sentence. */
  plain: string;
  description: string;
  /** Names of the coverage areas (`app/services/clinic_engine/v2/coverage_engine.py`) that belong here. */
  coverageAreas: string[];
  /** What to connect when nothing reports on this area. Only connectors that exist. */
  connectHint: string;
}

export const DOMAIN_CONFIG: Record<DomainKey, DomainConfig> = {
  identity: {
    title: 'Identity & Access',
    plain: 'sign-ins and accounts',
    description: 'Who can sign in to your systems, and what your connected systems report about those accounts.',
    coverageAreas: ['Users & Identities', 'Multi-Factor Authentication'],
    connectHint: 'Connect Microsoft 365 / Entra ID and the account checks ResilAI runs on it appear here.',
  },
  devices: {
    title: 'Devices & Workstations',
    plain: 'computers and devices',
    description: 'What your connected systems report about the computers and devices in the practice.',
    coverageAreas: ['Devices & Endpoints', 'Vulnerability Scanning'],
    connectHint: 'Connect Microsoft 365 or Wazuh and the device checks ResilAI runs on them appear here.',
  },
  backups: {
    title: 'Backups & Recovery',
    plain: 'backups',
    description: 'What your backup system reports about whether your data can be restored.',
    coverageAreas: ['Backup & Recovery', 'Local Backups'],
    connectHint: 'Connect Veeam Backup & Replication and the backup checks ResilAI runs on it appear here.',
  },
  email: {
    title: 'Email & Communication',
    plain: 'email',
    description: 'What your connected systems report about email protection.',
    coverageAreas: ['Email Security'],
    connectHint: 'Connect Microsoft 365 and anything ResilAI can check about email appears here.',
  },
  cloud: {
    title: 'Cloud Infrastructure',
    plain: 'cloud accounts',
    description: "What your cloud provider's own security service reports for your account.",
    coverageAreas: ['Cloud Security'],
    connectHint: 'Connect AWS and the findings AWS Security Hub reports for your account appear here.',
  },
  ai: {
    title: 'AI Tools & Agents',
    plain: 'AI tools',
    description: 'What ResilAI can verify about AI tools and agents used in the practice.',
    coverageAreas: [],
    connectHint: '',
  },
};

/** One check, whichever field names it arrived with (live API or typed sample). */
export interface DomainCheck {
  key: string;
  title: string;
  detail?: string;
  source?: string;
  age?: string;
}

const ACTION_CATEGORY_DOMAIN: Record<string, DomainKey> = {
  access_control: 'identity',
  device_security: 'devices',
  backup: 'backups',
  cloud_security: 'cloud',
};

/**
 * Decide which area a check belongs to. Order matters: the category the
 * backend attached to the check wins, then the capability label, then the
 * check's own wording. Returns null when the check belongs to none of them.
 */
export function classifyDomain(check: any): DomainKey | null {
  const actionCategory = String(check?.action?.category || '').toLowerCase();
  if (ACTION_CATEGORY_DOMAIN[actionCategory]) return ACTION_CATEGORY_DOMAIN[actionCategory];

  const label = `${check?.explanation?.technical_label || ''} ${check?.category || ''}`.toLowerCase();
  const fromLabel = matchDomain(label);
  if (fromLabel) return fromLabel;

  const wording = `${check?.label || ''} ${check?.name || ''} ${check?.system || ''} ${check?.source || ''} ${
    check?.verification?.verification_source || ''
  }`.toLowerCase();
  return matchDomain(wording);
}

function matchDomain(text: string): DomainKey | null {
  if (!text.trim()) return null;
  if (/\bcloud\b|\baws\b|amazon web services|\bazure\b|\bgcp\b|security hub|guardduty/.test(text)) return 'cloud';
  if (/backup|recovery|restore|snapshot|veeam/.test(text)) return 'backups';
  if (/e-?mail|phish|mailbox|spam/.test(text)) return 'email';
  if (/endpoint|device|workstation|laptop|antivirus|vulnerab|\bedr\b|intune|patch/.test(text)) return 'devices';
  if (/identity|\bmfa\b|multi-factor|sign-?in|log-?in|password|account|\buser|privilege/.test(text)) return 'identity';
  if (/\bai\b|\bllm\b|language model/.test(text)) return 'ai';
  return null;
}

function toCheck(raw: any, index: number, prefix: string): DomainCheck {
  return {
    key: `${prefix}-${raw?.check_id || raw?.id || index}`,
    title: String(raw?.label || raw?.name || raw?.system || 'Check'),
    detail: raw?.detail || raw?.description || raw?.impact || raw?.reason || undefined,
    source: raw?.verification?.verification_source || raw?.source || undefined,
    age: raw?.verification?.data_age_description || raw?.last_seen_description || undefined,
  };
}

export interface DomainSlice {
  failed: DomainCheck[];
  warnings: DomainCheck[];
  unknowns: DomainCheck[];
  passed: DomainCheck[];
  /** Coverage areas of this domain with the connected system that covers each, if any. */
  areas: { name: string; source: string | null }[];
  total: number;
  anyMonitored: boolean;
}

/** Cut one area out of a readiness report. Pure, so it can be tested without rendering. */
export function sliceReportForDomain(report: any, domain: DomainKey): DomainSlice {
  const pick = (items: any[] | undefined, prefix: string) =>
    (items || [])
      .filter((item) => classifyDomain(item) === domain)
      .map((item, index) => toCheck(item, index, prefix));

  const failed = pick(report?.failed_checks, 'fail');
  const warnings = pick(report?.warnings, 'warn');
  const unknowns = pick(report?.unknowns, 'unknown');
  const passed = pick(report?.passed_checks, 'pass');

  const wanted = DOMAIN_CONFIG[domain].coverageAreas;
  const monitored: any[] = report?.coverage?.monitored || [];
  const areas = wanted.map((name) => {
    const hit = monitored.find((a) => a?.area === name && a?.monitored !== false);
    return { name, source: hit ? String(hit.source || 'a connected system') : null };
  });

  return {
    failed,
    warnings,
    unknowns,
    passed,
    areas,
    total: failed.length + warnings.length + unknowns.length + passed.length,
    anyMonitored: areas.some((a) => a.source !== null),
  };
}

function formatWhen(iso?: string): string | null {
  if (!iso) return null;
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return null;
  return when.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

type Tone = 'critical' | 'warning' | 'unknown' | 'ready';

const TONE: Record<Tone, { dot: string; chip: string }> = {
  critical: { dot: 'bg-critical-red', chip: 'text-critical-red bg-critical-red/10' },
  warning: { dot: 'bg-drift-amber', chip: 'text-drift-amber bg-drift-amber/10' },
  unknown: { dot: 'bg-on-surface-variant', chip: 'text-on-surface-variant bg-surface-container' },
  ready: { dot: 'bg-ready-emerald', chip: 'text-ready-emerald bg-ready-emerald/10' },
};

function CheckList({ title, tone, checks, testId }: { title: string; tone: Tone; checks: DomainCheck[]; testId: string }) {
  if (checks.length === 0) return null;
  const style = TONE[tone];
  return (
    <section className="space-y-3" data-testid={testId}>
      <div className="flex items-center gap-3 pb-2 border-b border-outline-variant/30">
        <div className={`w-3 h-3 rounded-full ${style.dot}`} />
        <h2 className="text-lg font-semibold text-on-surface">{title}</h2>
        <span className={`ml-auto text-xs font-mono px-2.5 py-1 rounded-full ${style.chip}`}>{checks.length}</span>
      </div>
      <ul className="space-y-3">
        {checks.map((check) => (
          <li key={check.key} className="bg-surface-container-low rounded-xl p-4 border border-surface-bright">
            <p className="text-sm font-semibold text-on-surface">{check.title}</p>
            {check.detail && <p className="text-sm text-on-surface-variant mt-1">{check.detail}</p>}
            {(check.source || check.age) && (
              <p className="text-xs font-mono text-on-surface-variant mt-2">
                {[check.source && `Source: ${check.source}`, check.age].filter(Boolean).join(' · ')}
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

export interface DomainLiveViewProps {
  domain: DomainKey;
  icon: React.ElementType;
}

export function DomainLiveView({ domain, icon: Icon }: DomainLiveViewProps) {
  const config = DOMAIN_CONFIG[domain];
  const { orgId, loading: orgLoading } = useActiveOrg();
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await getDailyReadinessReport(orgId));
    } catch (err: any) {
      setError(err?.message || 'Could not load this area.');
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    load();
  }, [load]);

  if (orgLoading || loading) return <LoadingState message="Reading your connected systems..." />;
  if (error) return <ErrorState error={error} onRetry={load} />;

  const slice = sliceReportForDomain(report, domain);
  const generated = formatWhen(report?.generated_at);
  const nothingToShow = slice.total === 0 && !slice.anyMonitored;

  return (
    <div className="space-y-6 text-left max-w-5xl" data-testid={`domain-live-${domain}`}>
      <header className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-ready-emerald/30 bg-ready-emerald/15 text-ready-emerald">
          <Icon className="h-5 w-5" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-extrabold tracking-tight text-on-surface">{config.title}</h1>
          <p className="mt-0.5 max-w-3xl text-sm text-on-surface-variant">{config.description}</p>
          {generated && !nothingToShow && (
            <p className="mt-1 text-xs font-mono text-on-surface-variant">Read from your connected systems: {generated}</p>
          )}
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-surface-container text-xs font-semibold text-on-surface hover:bg-surface-container-high border border-outline-variant/40 transition-all shrink-0"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </header>

      {domain === 'ai' && slice.total === 0 ? (
        <div
          className="p-8 rounded-xl bg-surface-container-low border border-dashed border-surface-bright flex flex-col items-center justify-center text-center"
          data-testid="domain-empty-ai"
        >
          <h3 className="text-base font-semibold text-on-surface">ResilAI does not read AI tools through a connector yet.</h3>
          <p className="text-xs text-on-surface-variant max-w-md mt-1 leading-relaxed">
            Nothing on this page is measured for your organisation, so no numbers are shown.
          </p>
        </div>
      ) : nothingToShow ? (
        <ConnectFirstEmptyState
          title={`Nothing to show for ${config.plain} yet.`}
          body={`No connected system reports on ${config.plain}, so no numbers are shown. ${config.connectHint}`}
          testId={`domain-empty-${domain}`}
        />
      ) : (
        <>
          {slice.areas.length > 0 && (
            <section className="bg-surface-container-low rounded-xl p-5 border border-surface-bright" data-testid="domain-coverage">
              <h2 className="text-sm font-semibold text-on-surface">What ResilAI can see here</h2>
              <ul className="mt-3 space-y-2">
                {slice.areas.map((area) => (
                  <li key={area.name} className="flex flex-wrap items-center gap-2 text-sm">
                    <span className={`w-2 h-2 rounded-full ${area.source ? 'bg-ready-emerald' : 'bg-on-surface-variant'}`} />
                    <span className="text-on-surface">{area.name}</span>
                    <span className="text-on-surface-variant">
                      {area.source
                        ? `Connected through ${area.source}`
                        : slice.total > 0 && !slice.anyMonitored
                          ? 'No active connection. The items below were read earlier.'
                          : 'Not connected'}
                    </span>
                  </li>
                ))}
              </ul>
              {slice.areas.some((a) => a.source === null) && (
                <Link
                  to="/connectors"
                  className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-ready-emerald hover:underline"
                >
                  <Plug className="w-3.5 h-3.5" />
                  <span>Connect a system</span>
                </Link>
              )}
            </section>
          )}

          {slice.total === 0 ? (
            <div className="p-6 rounded-xl bg-surface-container-low border border-surface-bright" data-testid="domain-no-checks">
              <h3 className="text-base font-semibold text-on-surface">No checks have reported for this area.</h3>
              <p className="text-sm text-on-surface-variant mt-1">
                A system is connected, but the data read from it so far contains nothing ResilAI checks for{' '}
                {config.plain}. This is not a pass: it means nothing has been verified here.
              </p>
            </div>
          ) : (
            <>
              <CheckList title="Needs attention" tone="critical" checks={slice.failed} testId="domain-failed" />
              <CheckList title="Warnings" tone="warning" checks={slice.warnings} testId="domain-warnings" />
              <CheckList title="Could not be verified" tone="unknown" checks={slice.unknowns} testId="domain-unknowns" />
              <CheckList title="Passing" tone="ready" checks={slice.passed} testId="domain-passed" />
              {(slice.failed.length > 0 || slice.warnings.length > 0) && (
                <Link
                  to="/needs-attention"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-ready-emerald hover:underline"
                >
                  <span>See who should fix each item in Needs Attention</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

export default DomainLiveView;
