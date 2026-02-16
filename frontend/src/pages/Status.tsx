import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Activity, RefreshCw, Timer, Server, Bot, Boxes, Layers } from 'lucide-react';
import { Footer } from '../components/layout/Footer';
import { checkHealth, getSystemStatus, ApiRequestError, getApiBaseUrl } from '../api';
import type { ProductInfo, SystemStatus } from '../types';
import { Button } from '../components/ui';

interface StatusSnapshot {
  backendOperational: boolean | null;
  product: ProductInfo | null;
  system: SystemStatus | null;
  latencyMs: number | null;
  updatedAt: Date | null;
  error: string;
}

const AUTO_REFRESH_MS = 30000;

export default function StatusPage() {
  const [snapshot, setSnapshot] = useState<StatusSnapshot>({
    backendOperational: null,
    product: null,
    system: null,
    latencyMs: null,
    updatedAt: null,
    error: '',
  });
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const refreshStatus = useCallback(async () => {
    setRefreshing(true);
    const startedAt = performance.now();
    try {
      const [health, system] = await Promise.all([checkHealth(), getSystemStatus()]);
      const duration = Math.round(performance.now() - startedAt);
      setSnapshot({
        backendOperational: health.status === 'ok',
        product: health.product || null,
        system,
        latencyMs: duration,
        updatedAt: new Date(),
        error: '',
      });
    } catch (err) {
      setSnapshot((prev) => ({
        ...prev,
        backendOperational: false,
        updatedAt: new Date(),
        latencyMs: null,
        error: err instanceof ApiRequestError ? err.toDisplayMessage() : 'Unable to load status',
      }));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(refreshStatus, AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [autoRefresh, refreshStatus]);

  const apiBaseUrl = getApiBaseUrl();
  const payload = useMemo(
    () => ({
      backend_operational: snapshot.backendOperational,
      product: snapshot.product,
      system: snapshot.system,
      latency_ms: snapshot.latencyMs,
      updated_at: snapshot.updatedAt?.toISOString() || null,
      error: snapshot.error || null,
    }),
    [snapshot]
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-10 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">System Status</h1>
            <p className="text-slate-600 dark:text-slate-300 mt-2">
              Live platform health, deployment metadata, and runtime configuration.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={() => setAutoRefresh((value) => !value)}
            >
              <Timer className="h-4 w-4" />
              {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
            </Button>
            <Button size="sm" className="gap-2" onClick={refreshStatus} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {snapshot.error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
            {snapshot.error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatusCard
            icon={<Server className="h-4 w-4 text-blue-500" />}
            label="Backend"
            value={snapshot.backendOperational === null ? 'Checking...' : snapshot.backendOperational ? 'Operational' : 'Unavailable'}
          />
          <StatusCard
            icon={<Activity className="h-4 w-4 text-blue-500" />}
            label="Environment"
            value={snapshot.system?.environment || 'Unknown'}
          />
          <StatusCard
            icon={<Bot className="h-4 w-4 text-blue-500" />}
            label="LLM"
            value={snapshot.system?.llm_enabled ? 'Enabled' : 'Disabled'}
          />
          <StatusCard
            icon={<Layers className="h-4 w-4 text-blue-500" />}
            label="Version"
            value={snapshot.system?.version || snapshot.product?.version || 'Unknown'}
          />
          <StatusCard
            icon={<Boxes className="h-4 w-4 text-blue-500" />}
            label="Integrations"
            value={snapshot.system?.integrations_enabled ? 'Enabled' : 'Disabled'}
          />
          <StatusCard
            icon={<Timer className="h-4 w-4 text-blue-500" />}
            label="Latency"
            value={snapshot.latencyMs == null ? 'N/A' : `${snapshot.latencyMs} ms`}
          />
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Runtime Endpoints</h2>
          <div className="space-y-2 text-sm">
            <EndpointRow label="Health" href={`${apiBaseUrl}/health`} />
            <EndpointRow label="System" href={`${apiBaseUrl}/health/system`} />
            <EndpointRow label="LLM" href={`${apiBaseUrl}/health/llm`} />
            <EndpointRow label="CORS" href={`${apiBaseUrl}/health/cors`} />
          </div>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Last updated: {snapshot.updatedAt ? snapshot.updatedAt.toLocaleString() : 'Not yet loaded'}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">Raw Status Payload</h2>
          <pre className="text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-3 overflow-x-auto text-slate-700 dark:text-slate-200">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>
      </main>

      <Footer />
    </div>
  );
}

function StatusCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {icon}
        {label}
      </div>
      <div className="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">{value}</div>
    </div>
  );
}

function EndpointRow({ label, href }: { label: string; href: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md px-2 py-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
      <span className="text-slate-600 dark:text-slate-300">{label}</span>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="font-mono text-xs text-primary-600 dark:text-primary-300 hover:underline break-all text-right"
      >
        {href}
      </a>
    </div>
  );
}
