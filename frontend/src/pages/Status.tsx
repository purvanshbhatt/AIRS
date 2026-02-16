import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Activity, RefreshCw, Timer, Server, Bot, Boxes, Layers, ExternalLink, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
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

type EndpointState = 'idle' | 'checking' | 'ok' | 'error';

interface EndpointCheck {
  state: EndpointState;
  statusCode: number | null;
  durationMs: number | null;
  checkedAt: Date | null;
  error: string;
  preview: string;
}

interface EndpointConfig {
  key: string;
  label: string;
  path: string;
  description: string;
}

const AUTO_REFRESH_MS = 30000;
const ENDPOINT_TIMEOUT_MS = 10000;

const ENDPOINTS: EndpointConfig[] = [
  {
    key: 'health',
    label: 'Health',
    path: '/health',
    description: 'Core service liveness and product metadata.',
  },
  {
    key: 'system',
    label: 'System',
    path: '/health/system',
    description: 'Runtime environment, version, LLM, demo mode.',
  },
  {
    key: 'llm',
    label: 'LLM',
    path: '/health/llm',
    description: 'LLM runtime configuration checks.',
  },
  {
    key: 'cors',
    label: 'CORS',
    path: '/health/cors',
    description: 'Allowed origins and request-origin validation.',
  },
];

function createInitialEndpointChecks(): Record<string, EndpointCheck> {
  return ENDPOINTS.reduce<Record<string, EndpointCheck>>((acc, endpoint) => {
    acc[endpoint.key] = {
      state: 'idle',
      statusCode: null,
      durationMs: null,
      checkedAt: null,
      error: '',
      preview: '',
    };
    return acc;
  }, {});
}

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
  const [endpointChecks, setEndpointChecks] = useState<Record<string, EndpointCheck>>(createInitialEndpointChecks);

  const apiBaseUrl = getApiBaseUrl();

  const runEndpointCheck = useCallback(async (endpoint: EndpointConfig) => {
    setEndpointChecks((prev) => ({
      ...prev,
      [endpoint.key]: {
        ...prev[endpoint.key],
        state: 'checking',
        error: '',
      },
    }));

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), ENDPOINT_TIMEOUT_MS);
    const startedAt = performance.now();

    try {
      const response = await fetch(`${apiBaseUrl}${endpoint.path}`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });
      const duration = Math.round(performance.now() - startedAt);
      const raw = await response.text();
      const preview = raw.length > 240 ? `${raw.slice(0, 240)}...` : raw;

      if (!response.ok) {
        setEndpointChecks((prev) => ({
          ...prev,
          [endpoint.key]: {
            state: 'error',
            statusCode: response.status,
            durationMs: duration,
            checkedAt: new Date(),
            error: `HTTP ${response.status}`,
            preview,
          },
        }));
        return;
      }

      setEndpointChecks((prev) => ({
        ...prev,
        [endpoint.key]: {
          state: 'ok',
          statusCode: response.status,
          durationMs: duration,
          checkedAt: new Date(),
          error: '',
          preview,
        },
      }));
    } catch (err) {
      const duration = Math.round(performance.now() - startedAt);
      const message =
        err instanceof Error && err.name === 'AbortError'
          ? `Timed out after ${ENDPOINT_TIMEOUT_MS / 1000}s`
          : err instanceof Error
            ? err.message
            : 'Request failed';

      setEndpointChecks((prev) => ({
        ...prev,
        [endpoint.key]: {
          state: 'error',
          statusCode: null,
          durationMs: duration,
          checkedAt: new Date(),
          error: message,
          preview: '',
        },
      }));
    } finally {
      window.clearTimeout(timeout);
    }
  }, [apiBaseUrl]);

  const runAllEndpointChecks = useCallback(async () => {
    await Promise.all(ENDPOINTS.map((endpoint) => runEndpointCheck(endpoint)));
  }, [runEndpointCheck]);

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
    await runAllEndpointChecks();
  }, [runAllEndpointChecks]);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(() => {
      void refreshStatus();
    }, AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [autoRefresh, refreshStatus]);

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
            <Button
              size="sm"
              className="gap-2"
              onClick={() => {
                void refreshStatus();
              }}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh All
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
          <div className="flex items-center justify-between gap-3 mb-3">
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Interactive Endpoint Checks</h2>
            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={() => {
                void runAllEndpointChecks();
              }}
            >
              <RefreshCw className="h-4 w-4" />
              Re-run Checks
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {ENDPOINTS.map((endpoint) => (
              <EndpointCheckCard
                key={endpoint.key}
                endpoint={endpoint}
                result={endpointChecks[endpoint.key]}
                apiBaseUrl={apiBaseUrl}
                onRun={() => {
                  void runEndpointCheck(endpoint);
                }}
              />
            ))}
          </div>
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

function EndpointCheckCard({
  endpoint,
  result,
  apiBaseUrl,
  onRun,
}: {
  endpoint: EndpointConfig;
  result: EndpointCheck;
  apiBaseUrl: string;
  onRun: () => void;
}) {
  const href = `${apiBaseUrl}${endpoint.path}`;
  const statusLabel =
    result.state === 'idle'
      ? 'Not checked'
      : result.state === 'checking'
        ? 'Checking...'
        : result.state === 'ok'
          ? `OK${result.statusCode ? ` (${result.statusCode})` : ''}`
          : `Error${result.statusCode ? ` (${result.statusCode})` : ''}`;

  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 bg-slate-50 dark:bg-slate-950">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">{endpoint.label}</div>
          <div className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">{endpoint.description}</div>
        </div>
        <EndpointStateBadge state={result.state} label={statusLabel} />
      </div>

      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 inline-flex items-center gap-1 font-mono text-xs text-primary-600 dark:text-primary-300 hover:underline break-all"
      >
        {endpoint.path}
        <ExternalLink className="h-3.5 w-3.5" />
      </a>

      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {result.durationMs != null && <span>{result.durationMs} ms</span>}
          {result.durationMs != null && result.checkedAt && <span> • </span>}
          {result.checkedAt && <span>{result.checkedAt.toLocaleTimeString()}</span>}
          {result.durationMs == null && !result.checkedAt && <span>Awaiting check</span>}
        </div>
        <Button size="sm" variant="outline" onClick={onRun} className="gap-2">
          <RefreshCw className="h-3.5 w-3.5" />
          Run
        </Button>
      </div>

      {result.error && (
        <div className="mt-2 rounded border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-2 py-1.5 text-xs text-red-700 dark:text-red-300">
          {result.error}
        </div>
      )}

      {result.preview && (
        <pre className="mt-2 text-[11px] leading-relaxed text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded p-2 overflow-x-auto">
          {result.preview}
        </pre>
      )}
    </div>
  );
}

function EndpointStateBadge({ state, label }: { state: EndpointState; label: string }) {
  if (state === 'checking') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 text-[11px] text-blue-700 dark:text-blue-300">
        <Loader2 className="h-3 w-3 animate-spin" />
        {label}
      </span>
    );
  }

  if (state === 'ok') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/30 px-2 py-0.5 text-[11px] text-green-700 dark:text-green-300">
        <CheckCircle2 className="h-3 w-3" />
        {label}
      </span>
    );
  }

  if (state === 'error') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 text-[11px] text-red-700 dark:text-red-300">
        <AlertCircle className="h-3 w-3" />
        {label}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 py-0.5 text-[11px] text-slate-600 dark:text-slate-300">
      {label}
    </span>
  );
}
