import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  RefreshCw,
  Timer,
  Server,
  Bot,
  Boxes,
  Layers,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Lock,
  Cpu,
} from 'lucide-react';
import { Footer } from '../components/layout/Footer';
import { checkHealth, getSystemStatus, ApiRequestError, getApiBaseUrl } from '../api';
import type { ProductInfo, SystemStatus as SystemStatusType } from '../types';
import { Button } from '../components/ui';

interface StatusSnapshot {
  backendOperational: boolean | null;
  product: ProductInfo | null;
  system: SystemStatusType | null;
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
  const [countdownProgress, setCountdownProgress] = useState(100);
  const [endpointChecks, setEndpointChecks] = useState<Record<string, EndpointCheck>>(createInitialEndpointChecks);
  const [showRawPayload, setShowRawPayload] = useState(false);

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

  // Visual countdown progress bar
  useEffect(() => {
    if (!autoRefresh || refreshing) {
      setCountdownProgress(100);
      return;
    }

    const tickMs = 100;
    const totalTicks = AUTO_REFRESH_MS / tickMs;
    let currentTick = 0;

    const interval = setInterval(() => {
      currentTick += 1;
      const progress = Math.max(0, 100 - (currentTick / totalTicks) * 100);
      setCountdownProgress(progress);

      if (currentTick >= totalTicks) {
        currentTick = 0;
        void refreshStatus();
      }
    }, tickMs);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshing, refreshStatus]);

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
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-300">
      {/* Top Countdown bar */}
      <AnimatePresence>
        {autoRefresh && !refreshing && (
          <div className="fixed top-0 left-0 right-0 h-1 bg-slate-100 dark:bg-slate-900 z-50 overflow-hidden">
            <motion.div
              className="h-full bg-blue-500"
              initial={{ width: '100%' }}
              animate={{ width: `${countdownProgress}%` }}
              transition={{ ease: 'linear', duration: 0.1 }}
            />
          </div>
        )}
      </AnimatePresence>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-12 space-y-8 text-left">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-150 dark:border-slate-900 pb-6">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-950 dark:text-slate-50">System Status</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Real-time platform connectivity, AI core diagnostic metrics, and backend status.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              variant="outline"
              className="gap-2 text-xs rounded-xl"
              onClick={() => setAutoRefresh((value) => !value)}
            >
              <Timer className="h-4 w-4" />
              {autoRefresh ? 'Auto-Polling On' : 'Polling Off'}
            </Button>
            <Button
              size="sm"
              className="gap-2 text-xs bg-slate-900 hover:bg-slate-800 dark:bg-slate-50 dark:hover:bg-slate-100 text-white dark:text-slate-900 rounded-xl"
              onClick={() => {
                void refreshStatus();
              }}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Check Status
            </Button>
          </div>
        </div>

        {snapshot.error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-2xl text-xs text-rose-700 dark:text-rose-350">
            {snapshot.error}
          </div>
        )}

        {/* Services Status with Glowing/Pulsing Orbs */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Backend Status Card */}
          <div className="p-5 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5" />
                FastAPI Backend
              </span>
              <p className="text-base font-extrabold text-slate-900 dark:text-slate-550">
                {snapshot.backendOperational === null ? 'Loading...' : snapshot.backendOperational ? 'Operational' : 'Offline'}
              </p>
            </div>
            {/* Pulsing Orb */}
            <div className="relative flex items-center justify-center w-8 h-8">
              <div
                className={`absolute w-4 h-4 rounded-full opacity-35 animate-ping ${
                  snapshot.backendOperational ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              />
              <div
                className={`w-3.5 h-3.5 rounded-full border border-white/20 dark:border-black/20 shadow-md ${
                  snapshot.backendOperational ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-rose-500 shadow-rose-500/50'
                }`}
                style={{
                  boxShadow: `0 0 12px ${snapshot.backendOperational ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'}`,
                }}
              />
            </div>
          </div>

          {/* Gemini AI Engine Status Card */}
          <div className="p-5 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5" />
                Gemini Narrative Engine
              </span>
              <p className="text-base font-extrabold text-slate-900 dark:text-slate-550">
                {snapshot.system?.llm_enabled ? 'Ready / Active' : 'Offline'}
              </p>
            </div>
            {/* Pulsing Orb */}
            <div className="relative flex items-center justify-center w-8 h-8">
              {snapshot.system?.llm_enabled && (
                <div className="absolute w-4 h-4 rounded-full opacity-35 bg-emerald-500 animate-ping" />
              )}
              <div
                className={`w-3.5 h-3.5 rounded-full border border-white/20 dark:border-black/20 shadow-md ${
                  snapshot.system?.llm_enabled ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-rose-500 shadow-rose-500/50'
                }`}
                style={{
                  boxShadow: `0 0 12px ${snapshot.system?.llm_enabled ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'}`,
                }}
              />
            </div>
          </div>

          {/* Firebase Authentication Status Card */}
          <div className="p-5 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                Firebase Auth
              </span>
              <p className="text-base font-extrabold text-slate-900 dark:text-slate-550">
                {snapshot.system ? 'Active / Configured' : 'Offline'}
              </p>
            </div>
            {/* Pulsing Orb */}
            <div className="relative flex items-center justify-center w-8 h-8">
              {snapshot.system && (
                <div className="absolute w-4 h-4 rounded-full opacity-35 bg-emerald-500 animate-ping" />
              )}
              <div
                className={`w-3.5 h-3.5 rounded-full border border-white/20 dark:border-black/20 shadow-md ${
                  snapshot.system ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-rose-500 shadow-rose-500/50'
                }`}
                style={{
                  boxShadow: `0 0 12px ${snapshot.system ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'}`,
                }}
              />
            </div>
          </div>
        </div>

        {/* Latency Gauge & Metrics Row */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Latency Gauge Card */}
          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 space-y-4">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" />
                Latency Diagnostics
              </span>
              <p className="text-2xl font-extrabold mt-1">
                {snapshot.latencyMs === null ? 'N/A' : `${snapshot.latencyMs} ms`}
              </p>
            </div>
            {/* Visual Gauge Bar */}
            <div className="space-y-1.5">
              <div className="h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    snapshot.latencyMs === null
                      ? 'w-0'
                      : snapshot.latencyMs < 100
                        ? 'bg-emerald-500 w-1/4'
                        : snapshot.latencyMs < 300
                          ? 'bg-amber-500 w-2/4'
                          : 'bg-rose-500 w-4/4'
                  }`}
                />
              </div>
              <div className="flex justify-between text-[9px] font-bold text-slate-400">
                <span>Fast (&lt;100ms)</span>
                <span>Degraded (&gt;300ms)</span>
              </div>
            </div>
          </div>

          {/* System Environment details */}
          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 flex flex-col justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                Environment Deployment
              </span>
              <p className="text-base font-extrabold capitalize">
                {snapshot.system?.environment || 'Unknown'} Mode
              </p>
            </div>
            <div className="text-[10px] font-bold text-slate-400">
              API Version: {snapshot.system?.version || snapshot.product?.version || 'N/A'}
            </div>
          </div>

          {/* External Integrations */}
          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 flex flex-col justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5" />
                SIEM Integrations
              </span>
              <p className="text-base font-extrabold">
                {snapshot.system?.integrations_enabled ? 'Ready / Enabled' : 'Disabled'}
              </p>
            </div>
            <div className="text-[10px] font-bold text-slate-400">
              Wazuh &amp; Splunk active listeners
            </div>
          </div>
        </div>

        {/* Interactive Endpoint Check Cards */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-950 border border-slate-250 dark:border-slate-850 space-y-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-900 pb-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Live Endpoint Inspection</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Run specific health diagnostic routes.</p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="gap-2 text-xs rounded-xl"
              onClick={() => {
                void runAllEndpointChecks();
              }}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Re-run Checks
            </Button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
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

        {/* Runtime Endpoints Links */}
        <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">Runtime API Routes</h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-450 mt-0.5">Direct link to raw backend JSON payloads.</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 text-xs">
            <EndpointRow label="Health Diagnostics" href={`${apiBaseUrl}/health`} />
            <EndpointRow label="System Configurations" href={`${apiBaseUrl}/health/system`} />
            <EndpointRow label="LLM Narration State" href={`${apiBaseUrl}/health/llm`} />
            <EndpointRow label="CORS Access Controls" href={`${apiBaseUrl}/health/cors`} />
          </div>
        </div>

        {/* Raw Payload Section */}
        <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 overflow-hidden shadow-sm">
          <button
            onClick={() => setShowRawPayload(!showRawPayload)}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors"
          >
            <span className="text-sm font-bold text-slate-800 dark:text-slate-200">Raw Diagnostic JSON Payload</span>
            <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold">
              {showRawPayload ? 'Hide' : 'Expand'}
            </span>
          </button>

          {showRawPayload && (
            <div className="p-6 border-t border-slate-100 dark:border-slate-900 bg-slate-950">
              <pre className="text-[10px] leading-relaxed font-mono text-emerald-400 overflow-x-auto text-left whitespace-pre-wrap">
                {JSON.stringify(payload, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

function EndpointRow({ label, href }: { label: string; href: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl px-4 py-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-900">
      <span className="text-slate-600 dark:text-slate-400 font-semibold shrink-0">{label}</span>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="font-mono text-[10px] text-blue-600 dark:text-blue-400 hover:underline break-all text-right"
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
      ? 'Awaiting Check'
      : result.state === 'checking'
        ? 'Querying...'
        : result.state === 'ok'
          ? `HTTP ${result.statusCode || 200} OK`
          : `HTTP ${result.statusCode || 'FAIL'}`;

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-900 p-4 bg-slate-50 dark:bg-slate-900 flex flex-col justify-between gap-4 text-left">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{endpoint.label}</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal mt-0.5">{endpoint.description}</div>
          </div>
          <EndpointStateBadge state={result.state} label={statusLabel} />
        </div>

        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2.5 inline-flex items-center gap-1 font-mono text-[10px] text-blue-600 dark:text-blue-400 hover:underline break-all"
        >
          {endpoint.path}
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3 pt-2.5 border-t border-slate-100 dark:border-slate-850/60">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
            {result.durationMs != null && <span>Response: {result.durationMs} ms</span>}
            {result.durationMs != null && result.checkedAt && <span> • </span>}
            {result.checkedAt && <span>Checked: {result.checkedAt.toLocaleTimeString()}</span>}
            {result.durationMs == null && !result.checkedAt && <span>Not checked yet</span>}
          </div>
          <Button size="sm" variant="outline" onClick={onRun} className="gap-1.5 text-[10px] px-2.5 h-7 rounded-lg">
            <RefreshCw className="h-3 w-3" />
            Query
          </Button>
        </div>

        {result.error && (
          <div className="rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/20 px-3 py-2 text-[10px] text-rose-700 dark:text-rose-350">
            {result.error}
          </div>
        )}

        {result.preview && (
          <pre className="text-[10px] leading-relaxed text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-900 rounded-xl p-3 overflow-x-auto max-h-24">
            {result.preview}
          </pre>
        )}
      </div>
    </div>
  );
}

function EndpointStateBadge({ state, label }: { state: EndpointState; label: string }) {
  if (state === 'checking') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 dark:border-blue-900/30 bg-blue-50 dark:bg-blue-950/20 px-2.5 py-0.5 text-[10px] font-semibold text-blue-750 dark:text-blue-400 shrink-0">
        <Loader2 className="h-2.5 w-2.5 animate-spin" />
        {label}
      </span>
    );
  }

  if (state === 'ok') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-250 dark:border-emerald-900/30 bg-emerald-50 dark:bg-emerald-950/20 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-800 dark:text-emerald-400 shrink-0">
        <CheckCircle2 className="h-2.5 w-2.5 text-emerald-500" />
        {label}
      </span>
    );
  }

  if (state === 'error') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-rose-200 dark:border-rose-900/30 bg-rose-50 dark:bg-rose-950/20 px-2.5 py-0.5 text-[10px] font-semibold text-rose-800 dark:text-rose-400 shrink-0">
        <AlertCircle className="h-2.5 w-2.5 text-rose-500" />
        {label}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-905 px-2.5 py-0.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400 shrink-0">
      {label}
    </span>
  );
}
