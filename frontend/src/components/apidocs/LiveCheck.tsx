import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Loader2, Square } from 'lucide-react';
import { sendRawApiRequest } from '../../api';
import { MethodBadge, StateDot } from './EndpointDetail';
import {
  LIVE_CHECK_LIMIT,
  LIVE_CHECK_TIMEOUT_MS,
  buildRequestPath,
  classifyStatus,
  initialParameterValues,
  liveCheckCandidates,
  liveCheckEligible,
  type Endpoint,
  type LiveState,
  type OpenApiDocument,
} from './openapi';

interface StatusCheck {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
}

interface ReferenceStatus {
  api_version: string;
  build?: string | null;
  environment: string;
  server_time: string;
  demo_mode: boolean;
  read_only: boolean;
  endpoint_count: number;
  checks: StatusCheck[];
}

interface PingResult {
  endpoint: Endpoint;
  state: LiveState;
  status: number | null;
  durationMs: number | null;
  note?: string;
}

const STATE_LABEL: Record<LiveState, string> = {
  up: 'Working',
  'needs-input': 'Needs input',
  failing: 'Failing',
};

const LEGEND: Array<{ state: LiveState; text: string }> = [
  { state: 'up', text: 'The endpoint answered normally.' },
  {
    state: 'needs-input',
    text: 'The endpoint is reachable but wants something more: an id, a setting, or access your plan does not include.',
  },
  {
    state: 'failing',
    text: `The endpoint returned a server error or did not answer within ${LIVE_CHECK_TIMEOUT_MS / 1000} seconds.`,
  },
];

export interface LiveCheckProps {
  document: OpenApiDocument | null;
  endpoints: Endpoint[];
  orgId: string;
  /** Open an endpoint in the explorer. */
  onSelect?: (endpointId: string) => void;
}

/**
 * "Which APIs are live": asks the API for its own status, then calls each
 * read-only endpoint that needs nothing but the organisation id, one at a time.
 */
export function LiveCheck({ document, endpoints, orgId, onSelect }: LiveCheckProps) {
  const candidates = useMemo(() => liveCheckCandidates(endpoints), [endpoints]);
  const eligibleCount = useMemo(() => liveCheckEligible(endpoints).length, [endpoints]);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<ReferenceStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [results, setResults] = useState<PingResult[]>([]);
  const [hasRun, setHasRun] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const run = async () => {
    if (running) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setRunning(true);
    setHasRun(true);
    setStatus(null);
    setStatusError(null);
    setResults([]);

    try {
      const response = await sendRawApiRequest('/api/v1/reference/status', {
        timeoutMs: LIVE_CHECK_TIMEOUT_MS,
        signal: controller.signal,
      });
      if (response.ok) setStatus(JSON.parse(response.bodyText) as ReferenceStatus);
      else setStatusError(`The API status could not be read (status ${response.status}).`);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : 'The API status could not be read.');
    }

    for (const endpoint of candidates) {
      if (controller.signal.aborted) break;
      const built = buildRequestPath(endpoint, initialParameterValues(document, endpoint, orgId));
      let result: PingResult;
      if (built.missing.length > 0) {
        result = { endpoint, state: 'needs-input', status: null, durationMs: null, note: 'No organisation selected' };
      } else {
        try {
          const response = await sendRawApiRequest(built.path, {
            timeoutMs: LIVE_CHECK_TIMEOUT_MS,
            readBody: false,
            signal: controller.signal,
          });
          result = {
            endpoint,
            state: classifyStatus(response.status),
            status: response.status,
            durationMs: response.durationMs,
          };
        } catch (error) {
          if (controller.signal.aborted) break;
          result = {
            endpoint,
            state: 'failing',
            status: null,
            durationMs: null,
            note: error instanceof Error ? error.message : 'No answer',
          };
        }
      }
      setResults((current) => [...current, result]);
    }

    if (abortRef.current === controller) abortRef.current = null;
    setRunning(false);
  };

  const stop = () => abortRef.current?.abort();

  const counts = results.reduce(
    (acc, result) => ({ ...acc, [result.state]: acc[result.state] + 1 }),
    { up: 0, 'needs-input': 0, failing: 0 } as Record<LiveState, number>,
  );

  return (
    <section className="space-y-3 rounded-xl border border-outline-variant bg-surface-container-low p-3 sm:p-4" aria-label="Live check">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-extrabold text-on-surface">Live check</h3>
          <p className="text-xs text-on-surface-variant">
            See which parts of the API are working right now. It calls up to {LIVE_CHECK_LIMIT} read-only endpoints
            once each and changes nothing.
          </p>
        </div>
        {running ? (
          <button
            type="button"
            onClick={stop}
            className="inline-flex items-center gap-1.5 rounded-xl border border-outline-variant px-3 py-2 text-xs font-bold text-on-surface hover:bg-surface-container-high"
          >
            <Square className="h-3.5 w-3.5" aria-hidden />
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={run}
            className="inline-flex items-center gap-1.5 rounded-xl bg-on-surface px-3 py-2 text-xs font-bold text-surface-container-lowest hover:opacity-90"
          >
            <Activity className="h-3.5 w-3.5" aria-hidden />
            {hasRun ? 'Run again' : 'Run live check'}
          </button>
        )}
      </div>

      {hasRun && (
        <div className="space-y-3" aria-live="polite">
          {statusError && (
            <p role="alert" className="rounded-lg border border-critical-red/50 bg-critical-red/10 px-3 py-2 text-xs font-semibold text-on-surface">
              {statusError}
            </p>
          )}

          {status && (
            <div className="space-y-2" data-testid="live-status">
              <p className="text-xs text-on-surface-variant">
                API version <span className="font-semibold text-on-surface">{status.api_version}</span>
                {' · '}
                <span className="font-semibold text-on-surface">{status.environment}</span> environment
                {' · '}server time{' '}
                <span className="font-semibold text-on-surface">{new Date(status.server_time).toLocaleString()}</span>
              </p>
              <ul className="grid gap-1.5 sm:grid-cols-2">
                {status.checks.map((check) => (
                  <li key={check.id} className="flex items-start gap-2 rounded-lg border border-outline-variant bg-surface-container px-2.5 py-1.5 text-xs">
                    <span className="mt-1">
                      <StateDot state={check.ok ? 'up' : 'failing'} />
                    </span>
                    <span className="min-w-0">
                      <span className="font-bold text-on-surface">{check.label}</span>
                      <span className="block text-on-surface-variant">{check.detail}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant">
            {running && (
              <span className="inline-flex items-center gap-1.5 font-semibold text-on-surface">
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                Checking {Math.min(results.length + 1, candidates.length)} of {candidates.length}
              </span>
            )}
            {!running && results.length > 0 && (
              <span className="font-semibold text-on-surface" data-testid="live-summary">
                {counts.up} working, {counts['needs-input']} need input, {counts.failing} failing
              </span>
            )}
            {!running && eligibleCount > candidates.length && (
              <span>
                Checked {candidates.length} of the {eligibleCount} endpoints that can be checked automatically, a few
                from each area. Open any other endpoint and press Send to check it yourself.
              </span>
            )}
          </div>

          {results.length > 0 && (
            <ul className="divide-y divide-outline-variant rounded-lg border border-outline-variant" data-testid="live-results">
              {results.map((result) => (
                <li key={result.endpoint.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-2.5 py-1.5 text-xs">
                  <span className="inline-flex w-28 shrink-0 items-center gap-1.5 font-bold text-on-surface">
                    <StateDot state={result.state} />
                    {STATE_LABEL[result.state]}
                  </span>
                  <MethodBadge method={result.endpoint.method} />
                  <button
                    type="button"
                    onClick={() => onSelect?.(result.endpoint.id)}
                    className="min-w-0 flex-1 break-all text-left font-mono text-on-surface hover:underline"
                  >
                    {result.endpoint.path}
                  </button>
                  <span className="shrink-0 text-on-surface-variant">
                    {result.status !== null ? `${result.status} · ${result.durationMs} ms` : result.note}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <dl className="space-y-1 text-[11px] text-on-surface-variant">
            {LEGEND.map((item) => (
              <div key={item.state} className="flex items-start gap-2">
                <dt className="inline-flex w-24 shrink-0 items-center gap-1.5 font-bold text-on-surface">
                  <StateDot state={item.state} />
                  {STATE_LABEL[item.state]}
                </dt>
                <dd>{item.text}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </section>
  );
}

export default LiveCheck;
