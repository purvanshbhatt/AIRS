import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, LogIn, RefreshCw, Search } from 'lucide-react';
import { getApiBaseUrl, sendRawApiRequest } from '../../api';
import { useAuth } from '../../contexts/AuthContext';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import { EndpointDetail, MethodBadge } from './EndpointDetail';
import { LiveCheck } from './LiveCheck';
import { filterEndpoints, groupEndpoints, listEndpoints, type OpenApiDocument } from './openapi';

export interface ApiExplorerProps {
  /** Extra classes for the outer element. */
  className?: string;
  /** Heading above the explorer. Pass null to leave it out (when the host page has its own). */
  title?: string | null;
  /** Endpoint to open first, written as "method path", e.g. "get /api/v1/connectors". */
  initialEndpointId?: string;
  /** Shown under the sign-in notice when the visitor is not signed in. */
  signedOutFallback?: ReactNode;
}

type LoadState = 'loading' | 'ready' | 'signed-out' | 'error';

const REFERENCE_PATH = '/api/v1/reference/openapi';
const panel = 'rounded-2xl border border-outline-variant bg-surface-container-low text-on-surface';

function hostOf(baseUrl: string): string {
  try {
    return new URL(baseUrl, typeof window !== 'undefined' ? window.location.origin : 'http://localhost').host;
  } catch {
    return 'this deployment';
  }
}

/**
 * In-app API explorer: browse the endpoints your organisation can use, read
 * what each one takes and returns, run it with your own sign-in, and check
 * which ones are live. Requests only ever go to this deployment's API.
 */
export function ApiExplorer({ className = '', title = 'Try the API', initialEndpointId, signedOutFallback }: ApiExplorerProps) {
  const { user, loading: authLoading } = useAuth();
  const { orgId, orgName, isDemo } = useActiveOrg();
  const baseUrl = getApiBaseUrl();

  const [state, setState] = useState<LoadState>('loading');
  const [spec, setSpec] = useState<OpenApiDocument | null>(null);
  const [errorText, setErrorText] = useState('');
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(initialEndpointId ?? null);
  const detailRef = useRef<HTMLDivElement | null>(null);

  const signedIn = Boolean(user);

  const load = useCallback(async (signal?: AbortSignal) => {
    setState('loading');
    setErrorText('');
    try {
      const response = await sendRawApiRequest(REFERENCE_PATH, { maxBodyChars: 8_000_000, signal });
      if (signal?.aborted) return;
      if (response.status === 401 || response.status === 403) {
        setState('signed-out');
        return;
      }
      if (!response.ok || response.truncated) {
        setErrorText(`The API reference could not be loaded (status ${response.status}).`);
        setState('error');
        return;
      }
      setSpec(JSON.parse(response.bodyText) as OpenApiDocument);
      setState('ready');
    } catch (error) {
      if (signal?.aborted) return;
      setErrorText(error instanceof Error ? error.message : 'The API reference could not be loaded.');
      setState('error');
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!signedIn) {
      setState('signed-out');
      return;
    }
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [authLoading, signedIn, load]);

  const endpoints = useMemo(() => listEndpoints(spec), [spec]);
  const filtered = useMemo(() => filterEndpoints(endpoints, query), [endpoints, query]);
  const groups = useMemo(() => groupEndpoints(filtered), [filtered]);
  const selected = endpoints.find((endpoint) => endpoint.id === selectedId) ?? endpoints[0] ?? null;

  const select = (endpointId: string) => {
    setSelectedId(endpointId);
    // On a phone the detail sits under the list: bring it into view.
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      detailRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
    }
  };

  const heading = title ? <h2 className="text-lg font-extrabold tracking-tight text-on-surface">{title}</h2> : null;

  if (authLoading || state === 'loading') {
    return (
      <section className={`${panel} p-4 sm:p-5 ${className}`} aria-label="API explorer" aria-busy="true">
        {heading}
        <p className="mt-2 inline-flex items-center gap-2 text-sm text-on-surface-variant">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Loading the API reference
        </p>
      </section>
    );
  }

  if (state === 'signed-out') {
    return (
      <section className={`space-y-4 ${className}`} aria-label="API explorer">
        <div className={`${panel} flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5`}>
          <div className="min-w-0">
            <h2 className="text-lg font-extrabold tracking-tight text-on-surface">
              Sign in to try the API from here
            </h2>
            <p className="mt-0.5 max-w-2xl text-sm text-on-surface-variant">
              Once you are signed in, this page lists every endpoint your organisation can use and lets you run them
              without leaving ResilAI.
            </p>
          </div>
          <Link
            to="/login"
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-xl bg-on-surface px-4 py-2 text-sm font-bold text-surface-container-lowest hover:opacity-90"
          >
            <LogIn className="h-4 w-4" aria-hidden />
            Sign in
          </Link>
        </div>
        {signedOutFallback}
      </section>
    );
  }

  if (state === 'error') {
    return (
      <section className={`${panel} space-y-3 p-4 sm:p-5 ${className}`} aria-label="API explorer">
        {heading}
        <p role="alert" className="text-sm text-on-surface">
          {errorText}
        </p>
        <button
          type="button"
          onClick={() => load()}
          className="inline-flex items-center gap-1.5 rounded-xl border border-outline-variant px-3 py-2 text-xs font-bold text-on-surface hover:bg-surface-container-high"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          Try again
        </button>
      </section>
    );
  }

  const countText =
    filtered.length === endpoints.length
      ? `${endpoints.length} ${endpoints.length === 1 ? 'endpoint' : 'endpoints'}`
      : `${filtered.length} of ${endpoints.length} endpoints`;

  return (
    <section className={`space-y-4 text-left ${className}`} aria-label="API explorer">
      <header>
        {heading}
        <p className="mt-0.5 max-w-3xl text-sm text-on-surface-variant">
          Pick an endpoint, fill in what it asks for and press Send. Requests go to{' '}
          <span className="font-semibold text-on-surface">{hostOf(baseUrl)}</span> with your own sign-in
          {orgName ? (
            <>
              , as <span className="font-semibold text-on-surface">{orgName}</span>
            </>
          ) : null}
          .{isDemo ? ' This is the demo, so only requests that read data can be sent.' : ''}
        </p>
      </header>

      <LiveCheck document={spec} endpoints={endpoints} orgId={orgId} onSelect={select} />

      <div className={`${panel} grid lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]`}>
        <nav aria-label="Endpoints" className="min-w-0 border-b border-outline-variant p-3 lg:border-b-0 lg:border-r">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-on-surface-variant" aria-hidden />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search endpoints"
              aria-label="Search endpoints"
              className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest py-1.5 pl-8 pr-2.5 text-sm text-on-surface placeholder:text-on-surface-variant focus:border-ready-emerald focus:outline-none"
            />
          </div>
          <p className="mt-2 text-[11px] font-semibold text-on-surface-variant" data-testid="endpoint-count">
            {countText}
          </p>

          <div className="mt-2 max-h-72 space-y-3 overflow-y-auto pr-1 lg:max-h-[70vh]">
            {groups.length === 0 && (
              <p className="py-4 text-center text-xs text-on-surface-variant">No endpoint matches that search.</p>
            )}
            {groups.map((group) => (
              <div key={group.tag}>
                <h3 className="mb-1 flex items-center justify-between text-[11px] font-bold uppercase tracking-wide text-on-surface-variant">
                  <span>{group.label}</span>
                  <span>{group.endpoints.length}</span>
                </h3>
                <ul className="space-y-0.5">
                  {group.endpoints.map((endpoint) => {
                    const active = selected?.id === endpoint.id;
                    return (
                      <li key={endpoint.id}>
                        <button
                          type="button"
                          onClick={() => select(endpoint.id)}
                          aria-current={active ? 'true' : undefined}
                          className={`flex w-full items-start gap-2 rounded-lg border-l-2 px-2 py-1.5 text-left ${
                            active
                              ? 'border-ready-emerald bg-surface-container-high'
                              : 'border-transparent hover:bg-surface-container'
                          }`}
                        >
                          <span className="mt-0.5">
                            <MethodBadge method={endpoint.method} />
                          </span>
                          <span className="min-w-0">
                            <span className="block break-all font-mono text-[11px] font-semibold text-on-surface">
                              {endpoint.path}
                            </span>
                            <span className="block truncate text-[11px] text-on-surface-variant">{endpoint.summary}</span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </nav>

        <div ref={detailRef} className="min-w-0 scroll-mt-24 p-3 sm:p-5">
          {selected ? (
            <EndpointDetail
              key={selected.id}
              document={spec}
              endpoint={selected}
              baseUrl={baseUrl}
              orgId={orgId}
              orgName={orgName}
              writesDisabled={isDemo}
            />
          ) : (
            <p className="text-sm text-on-surface-variant">No endpoints are available for this account.</p>
          )}
        </div>
      </div>
    </section>
  );
}

export default ApiExplorer;
