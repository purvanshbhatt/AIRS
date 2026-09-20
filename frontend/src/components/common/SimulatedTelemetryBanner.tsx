import React from 'react';
import { Info, Sparkles } from 'lucide-react';

interface SimulatedTelemetryBannerProps {
  domainName: string;
}

export function SimulatedTelemetryBanner({ domainName }: SimulatedTelemetryBannerProps) {
  return (
    <div className="mb-6 p-4 rounded-xl bg-surface-container-low border border-outline-variant/50 flex items-start gap-3 text-xs text-on-surface-variant">
      <div className="p-1.5 rounded-lg bg-surface-container-high text-on-surface shrink-0 mt-0.5">
        <Sparkles className="w-4 h-4 text-drift-amber" />
      </div>
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-on-surface text-sm">
            {domainName ? `${domainName} — Operator Workspace Preview` : 'Operator Workspace Preview'}
          </span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-drift-amber/10 text-drift-amber border border-drift-amber/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span>Simulated Telemetry</span>
            <span>•</span>
            <span>DEMO ENVIRONMENT (SIMULATED DATA)</span>
          </span>
        </div>
        <p className="mt-1 leading-relaxed text-on-surface-variant">
          This deep technical domain view displays illustrative operator telemetry and simulated historical trends. Production readiness verification is calculated deterministically on the Morning Brief from live connector evidence.
        </p>
        <p className="mt-1 leading-relaxed text-drift-amber font-medium">
          This environment uses simulated security telemetry. Results shown here are not evidence from a connected customer environment.
        </p>
      </div>
    </div>
  );
}
