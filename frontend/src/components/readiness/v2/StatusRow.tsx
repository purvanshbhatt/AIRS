import { HardDrive, KeyRound, Laptop } from 'lucide-react';
import type { DailyReadinessReport, ReadinessCheck } from '../../../types/readiness';
import { StatusChip, type ChipStatus } from './StatusChip';

/**
 * Three-column status row: Backups / Logins & accounts / Devices.
 *
 * Each column is derived from the report's passed, failed and warning
 * checks by category/name pattern. A column with no matching check is
 * NOT CHECKED, never assumed verified.
 */

export type AreaKey = 'backups' | 'logins' | 'devices';

export interface AreaStatus {
  key: AreaKey;
  title: string;
  plain: string;
  status: ChipStatus;
  /** One plain sentence built from the matching check names. */
  detail: string;
  checkCount: number;
}

const AREA_PATTERNS: Record<AreaKey, RegExp> = {
  backups: /backup|recovery|snapshot|immutable|rpo|rto/i,
  logins: /mfa|identity|login|password|entra|credential|access|privilege|account/i,
  devices: /endpoint|device|edr|laptop|computer|encrypt|intune|patch|workstation/i,
};

const AREA_META: Record<AreaKey, { title: string; plain: string; Icon: typeof HardDrive }> = {
  backups: { title: 'Backups', plain: 'Can records be restored if computers are locked?', Icon: HardDrive },
  logins: { title: 'Logins & accounts', plain: 'Is the second login step (MFA) on for staff?', Icon: KeyRound },
  devices: { title: 'Devices', plain: 'Are computers protected and encrypted?', Icon: Laptop },
};

type TaggedCheck = ReadinessCheck & { state: 'passed' | 'failed' | 'warning' };

const joinNames = (checks: TaggedCheck[]) => checks.map(c => c.name).filter(Boolean).join(', ');

export function deriveAreaStatuses(report: DailyReadinessReport): AreaStatus[] {
  const all: TaggedCheck[] = [
    ...(report.passed_checks || []).map(c => ({ ...c, state: 'passed' as const })),
    ...(report.failed_checks || []).map(c => ({ ...c, state: 'failed' as const })),
    ...(report.warnings || []).map(c => ({ ...c, state: 'warning' as const })),
  ];

  return (Object.keys(AREA_PATTERNS) as AreaKey[]).map(key => {
    const matches = all.filter(c => AREA_PATTERNS[key].test(`${c.category || ''} ${c.name || ''}`));
    const meta = AREA_META[key];
    if (matches.length === 0) {
      return { key, title: meta.title, plain: meta.plain, status: 'not_checked', detail: 'No connected system reports on this yet.', checkCount: 0 };
    }
    const failed = matches.filter(c => c.state === 'failed');
    const warned = matches.filter(c => c.state === 'warning');
    if (failed.length > 0) {
      return { key, title: meta.title, plain: meta.plain, status: 'attention', detail: `${joinNames(failed)} did not pass.`, checkCount: matches.length };
    }
    if (warned.length > 0) {
      return { key, title: meta.title, plain: meta.plain, status: 'watch', detail: `${joinNames(warned)} needs a look soon.`, checkCount: matches.length };
    }
    return { key, title: meta.title, plain: meta.plain, status: 'verified', detail: `${joinNames(matches)} passed.`, checkCount: matches.length };
  });
}

const ICON_TONE: Record<ChipStatus, string> = {
  verified: 'bg-ready-emerald/10 border-ready-emerald/30 text-ready-emerald',
  attention: 'bg-critical-red/10 border-critical-red/30 text-critical-red',
  watch: 'bg-drift-amber/10 border-drift-amber/30 text-drift-amber',
  not_checked: 'bg-surface-container-high border-outline-variant/40 text-on-surface-variant',
};

export function StatusRow({ areas }: { areas: AreaStatus[] }) {
  return (
    <section aria-label="Status by area" className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="status-row">
      {areas.map(area => {
        const { Icon } = AREA_META[area.key];
        return (
          <div
            key={area.key}
            className="bg-surface-container-low border border-surface-bright/60 rounded-2xl p-5 sm:p-6 flex flex-col gap-4 m3-elevation-1"
            data-testid={`status-area-${area.key}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className={`w-10 h-10 rounded-xl border flex items-center justify-center shrink-0 ${ICON_TONE[area.status]}`}>
                <Icon className="w-5 h-5" aria-hidden="true" />
              </div>
              <StatusChip status={area.status} />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-bold text-on-surface">{area.title}</h3>
              <p className="text-xs text-on-surface-variant mt-0.5">{area.plain}</p>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed mt-auto">{area.detail}</p>
          </div>
        );
      })}
    </section>
  );
}
