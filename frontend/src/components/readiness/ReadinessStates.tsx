import React from 'react';
import { ShieldCheck, HelpCircle, AlertTriangle, Loader2 } from 'lucide-react';

export function HealthyState() {
  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4">
        <ShieldCheck className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-2">Everything is healthy</h3>
      <p className="text-slate-600 max-w-sm mx-auto">
        There is nothing requiring your attention today. We'll continue monitoring your systems and notify you if anything changes.
      </p>
    </div>
  );
}

export function UnknownState({ message = "We couldn't verify critical systems this morning. Readiness may be lower than shown." }: { message?: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-slate-200 text-slate-600 rounded-full flex items-center justify-center mb-4">
        <HelpCircle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-2">Telemetry Missing</h3>
      <p className="text-slate-600 max-w-sm mx-auto">
        {message}
      </p>
    </div>
  );
}

export function LoadingState({ message = "Gathering morning readiness data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      <p className="text-slate-500 font-medium">{message}</p>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: string, onRetry: () => void }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-2">Unable to Load Data</h3>
      <p className="text-red-700 max-w-sm mx-auto mb-6">
        {error}
      </p>
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}
