import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, HelpCircle, AlertTriangle, Loader2 } from 'lucide-react';

export function HealthyState() {
  return (
    <div className="rounded-3xl border border-ready-emerald/30 bg-surface-container-low p-8 text-center shadow-lg">
      <div className="mx-auto w-12 h-12 bg-ready-emerald/15 text-ready-emerald rounded-2xl flex items-center justify-center mb-4 border border-ready-emerald/30 shadow-xs">
        <ShieldCheck className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-on-surface mb-2">Everything is healthy</h3>
      <p className="text-on-surface-variant text-sm max-w-sm mx-auto leading-relaxed">
        There is nothing requiring your attention today. We'll continue monitoring your systems and notify you if anything changes.
      </p>
    </div>
  );
}

export function UnknownState({ message = "We couldn't verify critical systems this morning. Readiness may be lower than shown." }: { message?: string }) {
  return (
    <div className="rounded-3xl border border-drift-amber/30 bg-surface-container-low p-8 text-center shadow-lg">
      <div className="mx-auto w-12 h-12 bg-drift-amber/15 text-drift-amber rounded-2xl flex items-center justify-center mb-4 border border-drift-amber/30 shadow-xs">
        <HelpCircle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-on-surface mb-2">Telemetry Missing</h3>
      <p className="text-on-surface-variant text-sm max-w-sm mx-auto leading-relaxed">
        {message}
      </p>
    </div>
  );
}

export function LoadingState({ message = "Gathering morning readiness data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <Loader2 className="w-8 h-8 text-ready-emerald animate-spin" />
      <p className="text-on-surface-variant text-xs font-mono uppercase tracking-wider">{message}</p>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: string, onRetry: () => void }) {
  const isOrgMissing = error.toLowerCase().includes('organization') || error.toLowerCase().includes('not found') || error.toLowerCase().includes('resource');

  const handleResetWorkspace = () => {
    localStorage.removeItem('resilai_selected_org_id');
    window.location.href = '/onboarding';
  };

  const handleEnterDemo = () => {
    localStorage.setItem('resilai_demo_user', 'true');
    localStorage.setItem('resilai_selected_org_id', 'demo-health-org');
    window.location.href = '/morning-brief';
  };

  return (
    <div className="rounded-3xl border border-critical-red/30 bg-surface-container-low p-8 text-center shadow-2xl max-w-lg mx-auto">
      <div className="mx-auto w-12 h-12 bg-critical-red/15 text-critical-red rounded-2xl flex items-center justify-center mb-4 border border-critical-red/30 shadow-xs">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-on-surface mb-2">Unable to Load Data</h3>
      <p className="text-on-surface-variant text-sm max-w-md mx-auto mb-6 leading-relaxed">
        {error}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button 
          onClick={onRetry}
          className="px-5 py-2.5 bg-surface-container hover:bg-surface-container-high border border-outline-variant/60 rounded-xl text-sm font-semibold text-on-surface transition-all active:scale-[0.98] cursor-pointer"
        >
          Try Again
        </button>

        {isOrgMissing ? (
          <>
            <Link
              to="/onboarding?new=true"
              className="px-5 py-2.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 font-bold rounded-xl text-sm transition-all active:scale-[0.98] shadow-md shadow-ready-emerald/20"
            >
              Create Organization
            </Link>
            <button
              onClick={handleResetWorkspace}
              className="px-4 py-2.5 bg-surface-container hover:bg-surface-container-high border border-outline-variant/60 text-on-surface rounded-xl text-sm font-medium transition-all cursor-pointer"
            >
              Reset Workspace
            </button>
          </>
        ) : (
          <button
            onClick={handleEnterDemo}
            className="px-4 py-2.5 bg-drift-amber/15 hover:bg-drift-amber/25 border border-drift-amber/30 text-amber-600 dark:text-amber-400 rounded-xl text-sm font-semibold transition-all cursor-pointer shadow-xs"
          >
            Open Demo Sandbox
          </button>
        )}
      </div>
    </div>
  );
}

