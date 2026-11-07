/**
 * Status chip for the V2 morning brief.
 *
 * Four honest states, all derived from the report. No new colours: the
 * existing ready-emerald / drift-amber / critical-red tokens and the neutral
 * surface tokens are reused so the chip reads the same in light and dark.
 */

export type ChipStatus = 'verified' | 'attention' | 'watch' | 'not_checked';

export const CHIP_LABEL: Record<ChipStatus, string> = {
  verified: 'VERIFIED',
  attention: 'NEEDS ATTENTION',
  watch: 'WATCH',
  not_checked: 'NOT CHECKED',
};

const CHIP_CLASS: Record<ChipStatus, string> = {
  verified: 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/30',
  attention: 'bg-critical-red/10 text-critical-red border-critical-red/30',
  watch: 'bg-drift-amber/10 text-drift-amber border-drift-amber/30',
  not_checked: 'bg-surface-container-high text-on-surface-variant border-outline-variant/60',
};

const DOT_CLASS: Record<ChipStatus, string> = {
  verified: 'bg-ready-emerald',
  attention: 'bg-critical-red',
  watch: 'bg-drift-amber',
  not_checked: 'bg-outline',
};

export function StatusChip({ status, className = '' }: { status: ChipStatus; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-mono font-bold uppercase tracking-wider whitespace-nowrap ${CHIP_CLASS[status]} ${className}`}
      data-testid="status-chip"
      data-status={status}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${DOT_CLASS[status]}`} aria-hidden="true" />
      {CHIP_LABEL[status]}
    </span>
  );
}
