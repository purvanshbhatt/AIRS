import React, { useState } from 'react';
import { Globe, Loader2, Plus, ScanLine, Trash2, CheckCircle2, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import type { WebAsset, WebAssetScanResult } from '../../api';
import { TechnicalDetails } from '../readiness/PlainLanguage';
import { IssueList, formatDate, hostOf, normalizeWebUrl, plural, safeHttpUrl, timeAgo, toneText, type Tone } from './shared';

export interface WebAssetActionError {
  message: string;
  detail?: string;
}

interface WebAssetsPanelProps {
  assets: WebAsset[];
  /** Scan results from this session, keyed by asset id. */
  scans: Record<string, WebAssetScanResult>;
  scanningId: string | null;
  scanErrors: Record<string, WebAssetActionError>;
  readOnly?: boolean;
  /** Resolves on success, rejects with a WebAssetActionError-shaped object on failure. */
  onAdd: (data: { url: string; label: string }) => Promise<void>;
  onScan: (assetId: string) => void;
  onDelete: (assetId: string) => Promise<void>;
}

const HEADER_CHECKS: { key: keyof WebAssetScanResult['headers']; pass: string; fail: string; technical: string }[] = [
  {
    key: 'hsts',
    pass: 'Visitors are always sent to the secure version of the site',
    fail: 'Visitors are not forced onto the secure version of the site',
    technical: 'Strict-Transport-Security (HSTS)',
  },
  {
    key: 'csp',
    pass: 'The site limits which scripts are allowed to run',
    fail: 'The site does not limit which scripts are allowed to run',
    technical: 'Content-Security-Policy (CSP)',
  },
  {
    key: 'x_frame_options',
    pass: 'Other sites cannot hide your pages inside theirs to trick visitors',
    fail: 'Other sites could hide your pages inside theirs to trick visitors',
    technical: 'X-Frame-Options',
  },
  {
    key: 'x_content_type_options',
    pass: 'Browsers are told not to guess file types',
    fail: 'Browsers are allowed to guess file types, which attackers can abuse',
    technical: 'X-Content-Type-Options',
  },
  {
    key: 'referrer_policy',
    pass: 'The site limits what it tells other sites about your visitors',
    fail: 'The site does not limit what it tells other sites about your visitors',
    technical: 'Referrer-Policy',
  },
];

const CHECK_ICON: Record<Tone, React.ElementType> = {
  ready: CheckCircle2,
  warning: AlertTriangle,
  critical: XCircle,
  unknown: HelpCircle,
};

function Check({ tone, children, technical }: { tone: Tone; children: React.ReactNode; technical?: string }) {
  const Icon = CHECK_ICON[tone];
  return (
    <li className="flex items-start gap-2 text-sm text-on-surface" data-testid="web-check" data-tone={tone}>
      <Icon className={`w-4 h-4 shrink-0 mt-0.5 ${toneText[tone]}`} aria-hidden="true" />
      <span className="min-w-0">
        {children}
        {technical && <span className="block text-[10px] font-mono text-on-surface-variant/80">{technical}</span>}
      </span>
    </li>
  );
}

function tlsCheck(scan: WebAssetScanResult): { tone: Tone; text: string; technical?: string } {
  const tls = scan.tls;
  const isHttps = /^https:/i.test(scan.final_url || scan.url || '');
  if (!tls) {
    return isHttps
      ? { tone: 'unknown', text: 'We could not read the security certificate for this site.' }
      : {
          tone: 'critical',
          text: 'This address does not use a secure connection. Anything typed into it can be read by others on the network.',
          technical: 'No TLS (http)',
        };
  }
  const expires = formatDate(tls.expires_at);
  const technical = [tls.issuer ? `Issuer: ${tls.issuer}` : null, expires ? `Expires ${expires}` : null].filter(Boolean).join(' · ') || undefined;
  if (!tls.valid) {
    return {
      tone: 'critical',
      text: 'The security certificate is not valid. Visitors see a browser warning before they reach the site.',
      technical,
    };
  }
  if (typeof tls.days_left !== 'number') {
    return { tone: 'ready', text: 'The security certificate is valid.', technical };
  }
  if (tls.days_left < 0) {
    return { tone: 'critical', text: 'The security certificate has expired. Visitors see a browser warning.', technical };
  }
  if (tls.days_left <= 14) {
    return {
      tone: 'critical',
      text: `The security certificate expires in ${plural(tls.days_left, 'day', 'days')}. Ask IT to renew it now.`,
      technical,
    };
  }
  if (tls.days_left <= 30) {
    return {
      tone: 'warning',
      text: `The security certificate expires in ${plural(tls.days_left, 'day', 'days')}. Ask IT to renew it this month.`,
      technical,
    };
  }
  return { tone: 'ready', text: `The security certificate is valid for another ${plural(tls.days_left, 'day', 'days')}.`, technical };
}

function ScanResult({ scan }: { scan: WebAssetScanResult }) {
  const headers = scan.headers || ({} as WebAssetScanResult['headers']);
  const detected = scan.detected || [];
  const issues = scan.issues || [];
  const tls = tlsCheck(scan);
  const redirected = scan.final_url && scan.url && scan.final_url !== scan.url ? scan.final_url : null;

  return (
    <div className="space-y-4 pt-4 border-t border-outline-variant" data-testid="web-scan-result">
      <ul className="space-y-2">
        <Check
          tone={scan.reachable ? 'ready' : 'critical'}
          technical={[
            typeof scan.status_code === 'number' ? `HTTP ${scan.status_code}` : null,
            redirected ? `Redirects to ${redirected}` : null,
          ]
            .filter(Boolean)
            .join(' · ') || undefined}
        >
          {scan.reachable
            ? 'The site is up and answering visitors.'
            : 'The site did not answer. Visitors cannot reach it right now.'}
        </Check>
        {scan.reachable && (
          <Check tone={tls.tone} technical={tls.technical}>
            {tls.text}
          </Check>
        )}
      </ul>

      {scan.reachable && (
        <div>
          <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mb-2">
            Built-in browser protections
          </p>
          <ul className="space-y-2" data-testid="web-header-checks">
            {HEADER_CHECKS.map(h => {
              const on = Boolean(headers[h.key]);
              return (
                <Check key={h.key} tone={on ? 'ready' : 'warning'} technical={h.technical}>
                  {on ? h.pass : h.fail}
                </Check>
              );
            })}
          </ul>
        </div>
      )}

      {issues.length > 0 ? (
        <div>
          <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant mb-2">
            {plural(issues.length, 'thing', 'things')} to fix
          </p>
          <IssueList issues={issues} testId="web-issues" />
        </div>
      ) : (
        scan.reachable && <p className="text-sm text-on-surface-variant">The scan found nothing that needs fixing.</p>
      )}

      <TechnicalDetails title="Software this site runs" hint={`${detected.length} detected`} testId="web-detected">
        {detected.length === 0 ? (
          <p className="text-xs text-on-surface-variant">
            The site does not reveal which software it runs. That is normal for a well-configured site.
          </p>
        ) : (
          <ul className="space-y-2 text-xs">
            {detected.map((d, i) => (
              <li key={`${d.name}-${i}`} className="flex flex-col sm:flex-row sm:items-baseline sm:gap-3">
                <span className="font-semibold text-on-surface">
                  {d.name} <span className="font-mono font-normal">{d.version || 'version hidden'}</span>
                </span>
                {d.evidence && <span className="font-mono text-on-surface-variant break-all">{d.evidence}</span>}
              </li>
            ))}
          </ul>
        )}
      </TechnicalDetails>
    </div>
  );
}

function AssetCard({
  asset,
  scan,
  scanning,
  scanError,
  readOnly,
  onScan,
  onDelete,
}: {
  asset: WebAsset;
  scan: WebAssetScanResult | null;
  scanning: boolean;
  scanError?: WebAssetActionError;
  readOnly: boolean;
  onScan: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
}) {
  const [confirming, setConfirming] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [removeError, setRemoveError] = useState<string | null>(null);

  const lastScanAt = scan?.scanned_at || (typeof asset.last_scan === 'string' ? asset.last_scan : null);
  const ago = timeAgo(lastScanAt);
  const href = safeHttpUrl(asset.url);

  const remove = async () => {
    setRemoving(true);
    setRemoveError(null);
    try {
      await onDelete(asset.id);
    } catch (err) {
      setRemoveError((err as WebAssetActionError)?.message || 'We could not remove this address. Try again.');
      setRemoving(false);
      setConfirming(false);
    }
  };

  return (
    <li className="rounded-2xl border border-outline-variant bg-surface-container-low p-5 space-y-4" data-testid="web-asset-card">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-bold text-on-surface break-words">{asset.label || hostOf(asset.url)}</h3>
          {href ? (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono text-ready-emerald hover:underline break-all"
            >
              {asset.url}
            </a>
          ) : (
            <span className="text-xs font-mono text-on-surface-variant break-all">{asset.url}</span>
          )}
          <p className="mt-1 text-xs text-on-surface-variant" data-testid="web-last-scan">
            {ago ? `Last scanned ${ago}` : 'Not scanned yet'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => onScan(asset.id)}
            disabled={scanning || removing}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            data-testid="web-scan-button"
          >
            {scanning ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <ScanLine className="w-4 h-4" aria-hidden="true" />}
            {scanning ? 'Scanning...' : scan ? 'Scan again' : 'Scan'}
          </button>
          {!readOnly &&
            (confirming ? (
              <>
                <button
                  type="button"
                  onClick={remove}
                  disabled={removing}
                  className="px-3 py-2 rounded-xl border border-critical-red/40 bg-critical-red/10 text-critical-red text-sm font-semibold hover:bg-critical-red/20 disabled:opacity-60 cursor-pointer"
                  data-testid="web-remove-confirm"
                >
                  {removing ? 'Removing...' : 'Yes, remove'}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  disabled={removing}
                  className="px-3 py-2 rounded-xl border border-outline-variant text-on-surface-variant text-sm font-semibold hover:text-on-surface cursor-pointer"
                >
                  Keep
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setConfirming(true)}
                aria-label={`Remove ${asset.label || asset.url}`}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-outline-variant text-on-surface-variant text-sm font-semibold hover:text-critical-red hover:border-critical-red/40 transition-colors cursor-pointer"
                data-testid="web-remove-button"
              >
                <Trash2 className="w-4 h-4" aria-hidden="true" />
                Remove
              </button>
            ))}
        </div>
      </div>

      <div aria-live="polite" className="space-y-2">
        {scanning && (
          <p className="flex items-center gap-2 text-sm text-on-surface-variant" data-testid="web-scan-progress">
            <Loader2 className="w-4 h-4 animate-spin text-ready-emerald" aria-hidden="true" />
            Visiting the site the way a browser would. This takes a few seconds and does not change anything on it.
          </p>
        )}
        {!scanning && scanError && (
          <div className="rounded-xl border border-critical-red/30 bg-critical-red/10 p-3 text-sm text-on-surface" role="alert" data-testid="web-scan-error">
            <p className="font-semibold">{scanError.message}</p>
            {scanError.detail && <p className="mt-1 text-[11px] font-mono text-on-surface-variant break-words">{scanError.detail}</p>}
          </div>
        )}
        {removeError && (
          <p className="text-sm font-semibold text-critical-red" role="alert">
            {removeError}
          </p>
        )}
      </div>

      {scan && !scanning && <ScanResult scan={scan} />}
    </li>
  );
}

/** Websites and apps: add an address, scan it, read the result as plain checks. */
export function WebAssetsPanel({
  assets,
  scans,
  scanningId,
  scanErrors,
  readOnly = false,
  onAdd,
  onScan,
  onDelete,
}: WebAssetsPanelProps) {
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    const checked = normalizeWebUrl(url);
    if ('error' in checked) {
      setFormError(checked.error);
      return;
    }
    if ((assets || []).some(a => safeHttpUrl(a.url) === checked.url)) {
      setFormError('That address is already on your list.');
      return;
    }
    setFormError(null);
    setSaving(true);
    try {
      await onAdd({ url: checked.url, label: label.trim() || hostOf(checked.url) });
      setUrl('');
      setLabel('');
    } catch (err) {
      setFormError((err as WebAssetActionError)?.message || 'We could not save that address. Try again.');
    } finally {
      setSaving(false);
    }
  };

  const list = assets || [];

  return (
    <div className="space-y-5" data-testid="web-assets-panel">
      {!readOnly && (
        <form
          onSubmit={submit}
          noValidate
          className="rounded-2xl border border-outline-variant bg-surface-container-low p-5 space-y-3"
          data-testid="web-asset-form"
        >
          <div>
            <h3 className="text-base font-bold text-on-surface">Add a website or web app</h3>
            <p className="text-sm text-on-surface-variant mt-0.5 leading-relaxed">
              Your public website, patient or client portal, or booking page. We only look at what any visitor can see.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_auto] gap-3 md:items-end">
            <div>
              <label htmlFor="web-asset-url" className="block text-xs font-semibold text-on-surface mb-1">
                Web address
              </label>
              <input
                id="web-asset-url"
                type="url"
                inputMode="url"
                autoComplete="url"
                value={url}
                onChange={e => {
                  setUrl(e.target.value);
                  if (formError) setFormError(null);
                }}
                placeholder="https://www.yourpractice.com"
                aria-invalid={formError ? 'true' : 'false'}
                aria-describedby={formError ? 'web-asset-error' : undefined}
                className="w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:outline-none focus:ring-2 focus:ring-ready-emerald/30"
              />
            </div>
            <div>
              <label htmlFor="web-asset-label" className="block text-xs font-semibold text-on-surface mb-1">
                Name <span className="font-normal text-on-surface-variant">(optional)</span>
              </label>
              <input
                id="web-asset-label"
                type="text"
                value={label}
                maxLength={80}
                onChange={e => setLabel(e.target.value)}
                placeholder="Patient portal"
                className="w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:outline-none focus:ring-2 focus:ring-ready-emerald/30"
              />
            </div>
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
              data-testid="web-asset-add"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />}
              {saving ? 'Adding...' : 'Add'}
            </button>
          </div>
          {formError && (
            <p id="web-asset-error" className="text-sm font-semibold text-critical-red" role="alert" data-testid="web-asset-error">
              {formError}
            </p>
          )}
        </form>
      )}

      {list.length === 0 ? (
        <div
          className="p-8 rounded-xl bg-surface-container-low border border-dashed border-outline-variant flex flex-col items-center text-center"
          data-testid="web-assets-empty"
        >
          <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
            <Globe className="w-6 h-6" aria-hidden="true" />
          </div>
          <h3 className="text-base font-semibold text-on-surface">No websites added yet</h3>
          <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
            {readOnly
              ? 'This workspace has no websites on its list.'
              : 'Add your website address above, then press "Scan". You get a plain list of what is fine and what to fix.'}
          </p>
        </div>
      ) : (
        <ul className="space-y-4">
          {list.map(asset => {
            const stored = asset.last_scan && typeof asset.last_scan === 'object' ? asset.last_scan : null;
            return (
              <AssetCard
                key={asset.id}
                asset={asset}
                scan={scans[asset.id] || stored}
                scanning={scanningId === asset.id}
                scanError={scanErrors[asset.id]}
                readOnly={readOnly}
                onScan={onScan}
                onDelete={onDelete}
              />
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default WebAssetsPanel;
