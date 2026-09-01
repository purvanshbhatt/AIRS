import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, HelpCircle, AlertTriangle, Loader2 } from 'lucide-react';

export function HealthyState() {
  return (
    <div className="rounded-3xl border border-emerald-500/30 bg-emerald-500/10 p-8 text-center shadow-lg">
      <div className="mx-auto w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-2xl flex items-center justify-center mb-4 border border-emerald-500/40">
        <ShieldCheck className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2">Everything is healthy</h3>
      <p className="text-slate-300 text-sm max-w-sm mx-auto leading-relaxed">
        There is nothing requiring your attention today. We'll continue monitoring your systems and notify you if anything changes.
      </p>
    </div>
  );
}

export function UnknownState({ message = "We couldn't verify critical systems this morning. Readiness may be lower than shown." }: { message?: string }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 text-center shadow-lg">
      <div className="mx-auto w-12 h-12 bg-slate-800 text-amber-400 rounded-2xl flex items-center justify-center mb-4 border border-slate-700">
        <HelpCircle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2">Telemetry Missing</h3>
      <p className="text-slate-300 text-sm max-w-sm mx-auto leading-relaxed">
        {message}
      </p>
    </div>
  );
}

export function LoadingState({ message = "Gathering morning readiness data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
      <p className="text-slate-400 text-xs font-mono uppercase tracking-wider">{message}</p>
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
    <div className="rounded-3xl border border-red-500/30 bg-slate-900/90 p-8 text-center shadow-2xl max-w-lg mx-auto">
      <div className="mx-auto w-12 h-12 bg-red-500/20 text-red-400 rounded-2xl flex items-center justify-center mb-4 border border-red-500/40">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2">Unable to Load Data</h3>
      <p className="text-slate-300 text-sm max-w-md mx-auto mb-6 leading-relaxed">
        {error}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button 
          onClick={onRetry}
          className="px-5 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-sm font-semibold text-slate-200 hover:text-white hover:bg-slate-700 transition-all active:scale-[0.98]"
        >
          Try Again
        </button>

        {isOrgMissing ? (
          <>
            <Link
              to="/onboarding?new=true"
              className="px-5 py-2.5 bg-gradient-to-br from-primary-600 to-emerald-500 text-white rounded-xl text-sm font-semibold hover:shadow-lg transition-all active:scale-[0.98]"
            >
              Create Organization
            </Link>
            <button
              onClick={handleResetWorkspace}
              className="px-4 py-2.5 bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white rounded-xl text-sm font-medium transition-all"
            >
              Reset Workspace
            </button>
          </>
        ) : (
          <button
            onClick={handleEnterDemo}
            className="px-4 py-2.5 bg-slate-800/80 border border-slate-700 text-amber-400 hover:text-amber-300 rounded-xl text-sm font-medium transition-all"
          >
            Open Demo Sandbox
          </button>
        )}
      </div>
    </div>
  );
}

