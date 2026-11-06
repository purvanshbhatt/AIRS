import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronUp, Server, Plug, ArrowRight, UserCog, Clock } from 'lucide-react';
import type { DailyReadinessReport } from '../../types/readiness';

/**
 * Plain-language helpers for the readiness pages.
 *
 * Everything here is deterministic: copy is derived from report fields
 * (status, score, failed checks, backup state). No numbers are invented;
 * when a count is shown it comes straight from the report.
 */

export type VerdictTone = 'ready' | 'warning' | 'critical' | 'unknown';

export interface PlainVerdict {
  tone: VerdictTone;
  /** One sentence a non-technical reader understands. */
  verdict: string;
  /** One line: what to do today. */
  today: string;
  failedCount: number;
  backupVerified: boolean | null;
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

function hasBackupFailure(report: DailyReadinessReport): boolean {
  const isBackup = (c: { name?: string; category?: string }) =>
    /backup|recovery|snapshot|immutable/i.test(`${c.category || ''} ${c.name || ''}`);
  return (report.failed_checks || []).some(isBackup);
}

export function derivePlainVerdict(report: DailyReadinessReport): PlainVerdict {
  const status = String(report.status || '').toLowerCase();
  const pct = Number(report.clinic_health_pct || 0);
  const failedCount = (report.failed_checks || []).length || (report.immediate_actions || []).length;
  const readiness = report.business_continuity?.operational_readiness;
  const canOperate = readiness?.can_operate_today;
  const backupVerified: boolean | null =
    typeof readiness?.can_recover === 'boolean'
      ? readiness.can_recover && !hasBackupFailure(report)
      : hasBackupFailure(report)
        ? false
        : null;

  const isUnknown =
    status === 'unknown' ||
    (report.verification && report.verification.overall_confidence_pct === 0) ||
    (!pct && failedCount === 0);

  if (isUnknown) {
    return {
      tone: 'unknown',
      verdict: 'We cannot tell yet whether your practice is protected.',
      today: 'Today: connect your first system so the checks can run.',
      failedCount,
      backupVerified,
    };
  }

  const isCritical = status === 'critical_risk' || canOperate === false || pct < 50;
  if (isCritical) {
    const count = failedCount > 0 ? plural(failedCount, 'thing needs', 'things need') : 'Something needs';
    return {
      tone: 'critical',
      verdict: `Your practice is not protected right now. ${count} fixing today.`,
      today:
        backupVerified === false
          ? 'Today: call your IT provider before opening. Backups come first, then the rest of the list.'
          : 'Today: call your IT provider before opening. Start with the item marked critical below.',
      failedCount,
      backupVerified,
    };
  }

  const isReady = status === 'safe_to_open' || (pct >= 90 && failedCount === 0);
  if (isReady) {
    if (backupVerified === false) {
      return {
        tone: 'warning',
        verdict: 'Your systems look healthy, but we cannot confirm your backups would bring you back.',
        today: 'Today: ask IT to confirm the last backup completed and can be restored.',
        failedCount,
        backupVerified,
      };
    }
    return {
      tone: 'ready',
      verdict: 'You can keep operating if something goes wrong tonight.',
      today: 'Today: nothing needs your time. We keep checking around the clock and will tell you if that changes.',
      failedCount,
      backupVerified,
    };
  }

  const count = failedCount > 0 ? plural(failedCount, 'thing needs', 'things need') : 'Something needs';
  return {
    tone: 'warning',
    verdict: `${count} attention before you are fully protected.`,
    today:
      backupVerified === false
        ? 'Today: send the backup item below to whoever handles your IT. Fix that one first.'
        : 'Today: send the first item below to whoever handles your IT. The rest is being watched.',
    failedCount,
    backupVerified,
  };
}

export const verdictToneClass: Record<VerdictTone, string> = {
  ready: 'text-ready-emerald',
  warning: 'text-drift-amber',
  critical: 'text-critical-red',
  unknown: 'text-on-surface-variant',
};

/* ------------------------------------------------------------------------- */
/* Per-check guidance                                                         */
/* ------------------------------------------------------------------------- */

export interface CheckGuidanceInput {
  title?: string;
  category?: string;
  severity?: string;
  detail?: string;
  whyItMatters?: string;
  action?: string;
  /** Backend-provided estimate, when present. Never invented here. */
  estimatedMinutes?: number | null;
}

/**
 * The live backend and the typed mock use different field names for an
 * action card (`id`/`action_id`, `title`/`problem`, `recommendation`/
 * `recommended_action`, ...). Normalise both into one shape for display.
 */
export interface NormalizedAction {
  id: string;
  title: string;
  severity?: string;
  category?: string;
  whatHappened?: string;
  whyItMatters?: string;
  recommendation?: string;
  lastVerifiedAt?: string;
  estimatedMinutes?: number | null;
}

export function normalizeAction(a: any, index = 0): NormalizedAction {
  const explanation = a?.explanation;
  return {
    id: String(a?.id || a?.action_id || a?.title || a?.problem || `action-${index}`),
    title: explanation?.business_label || a?.title || a?.problem || 'Needs attention',
    severity: a?.severity,
    category: explanation?.technical_label || a?.category,
    whatHappened: explanation?.what_it_means || a?.impact_narrative || a?.description || a?.detail,
    whyItMatters: explanation?.why_it_matters || a?.why_it_matters,
    recommendation: explanation?.what_to_do_next || a?.recommendation || a?.recommended_action,
    lastVerifiedAt: a?.last_verified_at || a?.verification?.last_verified_at || undefined,
    estimatedMinutes: typeof a?.estimated_time_minutes === 'number' ? a.estimated_time_minutes : null,
  };
}

export function guidanceForAction(action: NormalizedAction): CheckGuidance {
  return deriveCheckGuidance({
    title: action.title,
    category: action.category,
    severity: action.severity,
    detail: action.whatHappened,
    whyItMatters: action.whyItMatters,
    action: action.recommendation,
    estimatedMinutes: action.estimatedMinutes,
  });
}

export interface CheckGuidance {
  whatHappened: string;
  whyItMatters: string;
  whoFixes: string;
  howLong: string;
  plainCategory: string;
}

type CheckKind = 'backup' | 'identity' | 'device' | 'email' | 'network' | 'monitoring' | 'other';

function classifyCheck(input: CheckGuidanceInput): CheckKind {
  const text = `${input.category || ''} ${input.title || ''}`.toLowerCase();
  if (/backup|recovery|snapshot|immutable|rpo|rto/.test(text)) return 'backup';
  if (/mfa|identity|login|password|entra|credential|access|privilege/.test(text)) return 'identity';
  if (/endpoint|device|edr|laptop|computer|encrypt|intune|patch/.test(text)) return 'device';
  if (/email|phishing|mail/.test(text)) return 'email';
  if (/tls|certificate|network|firewall|dns|vpn/.test(text)) return 'network';
  if (/monitor|log|telemetry|siem|splunk|alert/.test(text)) return 'monitoring';
  return 'other';
}

const KIND_COPY: Record<CheckKind, { plain: string; why: string; who: string }> = {
  backup: {
    plain: 'Backups',
    why: 'If an attacker locks your computers, backups are the only way to get patient and client records back without paying.',
    who: 'IT / MSP',
  },
  identity: {
    plain: 'Staff logins',
    why: 'A stolen password is the most common way attackers get in. The second login step (MFA) stops most of them.',
    who: 'IT / MSP',
  },
  device: {
    plain: 'Computers and devices',
    why: 'An unprotected computer lets an attacker move between computers and reach your records.',
    who: 'IT / MSP',
  },
  email: {
    plain: 'Email',
    why: 'Most attacks start with an email. Filtering catches them before a staff member clicks.',
    who: 'IT / MSP',
  },
  network: {
    plain: 'Network and website',
    why: 'An expired certificate or open network setting can take systems offline or expose data.',
    who: 'IT / MSP',
  },
  monitoring: {
    plain: 'Monitoring',
    why: 'Without live data from this system we cannot confirm it is protected, so the score may be lower than reality.',
    who: 'IT / MSP',
  },
  other: {
    plain: 'Security check',
    why: 'This check failed, so part of your protection cannot be confirmed right now.',
    who: 'IT / MSP',
  },
};

function severityToDuration(severity?: string, kind?: CheckKind): string {
  const s = String(severity || '').toLowerCase();
  if (kind === 'monitoring') return 'Usually a quick reconnect once IT has the login details';
  if (s === 'critical') return 'Usually done the same day once IT starts';
  if (s === 'high') return 'Usually done the same day once IT starts';
  if (s === 'medium') return 'Usually fits in a routine IT visit';
  if (s === 'low') return 'Usually fits in a routine IT visit';
  return 'Usually done the same day once IT starts';
}

export function deriveCheckGuidance(input: CheckGuidanceInput): CheckGuidance {
  const kind = classifyCheck(input);
  const base = KIND_COPY[kind];
  const who =
    kind === 'identity' && /password|office|front desk|reception/i.test(input.title || '')
      ? 'Office manager with IT'
      : base.who;
  const howLong =
    typeof input.estimatedMinutes === 'number' && input.estimatedMinutes > 0
      ? `About ${input.estimatedMinutes} minute${input.estimatedMinutes === 1 ? '' : 's'} once IT starts`
      : severityToDuration(input.severity, kind);
  return {
    whatHappened: input.detail || input.title || 'A security check did not pass.',
    whyItMatters: input.whyItMatters || base.why,
    whoFixes: who,
    howLong,
    plainCategory: base.plain,
  };
}

/* ------------------------------------------------------------------------- */
/* Small UI pieces (existing look, no new colours)                            */
/* ------------------------------------------------------------------------- */

/** Plain label with the technical term kept as a smaller secondary line. */
export function PlainTerm({
  plain,
  technical,
  className = '',
}: {
  plain: string;
  technical?: string;
  className?: string;
}) {
  return (
    <span className={`inline-flex flex-col leading-tight ${className}`}>
      <span>{plain}</span>
      {technical && (
        <span className="text-[10px] font-mono text-on-surface-variant/70 normal-case tracking-normal">{technical}</span>
      )}
    </span>
  );
}

/** "Who should fix it" and "How long it usually takes" strip for a check card. */
export function CheckOwnerStrip({ guidance, className = '' }: { guidance: CheckGuidance; className?: string }) {
  return (
    <div
      className={`grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs ${className}`}
      data-testid="check-owner-strip"
    >
      <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-surface-bright/40">
        <UserCog className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
        <span className="text-on-surface-variant">
          <strong className="text-on-surface block">Who should fix it</strong>
          {guidance.whoFixes}
        </span>
      </div>
      <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-container border border-surface-bright/40">
        <Clock className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
        <span className="text-on-surface-variant">
          <strong className="text-on-surface block">How long it usually takes</strong>
          {guidance.howLong}
        </span>
      </div>
    </div>
  );
}

/** Collapsible technical section, same style as the evidence accordion. */
export function TechnicalDetails({
  title = 'Technical details',
  hint,
  defaultOpen = false,
  children,
  className = '',
  testId = 'technical-details',
}: {
  title?: string;
  hint?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  className?: string;
  testId?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div
      className={`border border-surface-bright/60 rounded-xl overflow-hidden bg-surface-container-lowest/60 ${className}`}
      data-testid={testId}
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <Server className="w-4 h-4 text-ready-emerald" />
          <span>{title}</span>
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[11px] lowercase font-normal opacity-70">
            {open ? 'hide' : hint || 'for your IT provider'}
          </span>
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>
      {open && <div className="p-5 border-t border-surface-bright/40 space-y-4">{children}</div>}
    </div>
  );
}

/** Empty state for a real org with no connected systems. */
export function ConnectFirstEmptyState({
  title = 'Nothing to show yet: no systems are connected.',
  body = 'Connect your backup system (for example Veeam) or Microsoft 365 first. That is where most practices get their first answer. Each takes one login from your IT provider.',
  testId = 'connect-first-empty-state',
}: {
  title?: string;
  body?: string;
  testId?: string;
}) {
  return (
    <div
      className="p-8 rounded-xl bg-surface-container-low border border-dashed border-surface-bright flex flex-col items-center justify-center text-center"
      data-testid={testId}
    >
      <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
        <Plug className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-on-surface">{title}</h3>
      <p className="text-xs text-on-surface-variant max-w-md mt-1 leading-relaxed">{body}</p>
      <Link
        to="/connectors"
        className="mt-4 inline-flex items-center gap-2 px-6 py-3 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl transition-all active:scale-[0.98]"
      >
        <Plug className="w-4 h-4" />
        <span>Connect a system</span>
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}
