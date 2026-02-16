import { useEffect, useState } from 'react';
import { Footer } from '../components/layout/Footer';
import { checkHealth, getSystemStatus, ApiRequestError } from '../api';
import type { SystemStatus } from '../types';

export default function StatusPage() {
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        const [health, status] = await Promise.all([checkHealth(), getSystemStatus()]);
        setHealthOk(health.status === 'ok');
        setSystem(status);
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Unable to load status');
      }
    };
    run();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-10 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">System Status</h1>
          <p className="text-slate-600 mt-2">Public status for platform health and runtime configuration.</p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{error}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatusCard label="Backend" value={healthOk === null ? 'Checking...' : healthOk ? 'Operational' : 'Unavailable'} />
          <StatusCard label="Environment" value={system?.environment || 'Unknown'} />
          <StatusCard label="LLM" value={system?.llm_enabled ? 'Enabled' : 'Disabled'} />
          <StatusCard label="Version" value={system?.version || 'Unknown'} />
          <StatusCard label="Integrations" value={system?.integrations_enabled ? 'Enabled' : 'Disabled'} />
          <StatusCard label="Last Deployment" value={system?.last_deployment_at || 'Not reported'} />
        </div>
      </main>

      <Footer />
    </div>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-base font-semibold text-slate-900">{value}</div>
    </div>
  );
}

