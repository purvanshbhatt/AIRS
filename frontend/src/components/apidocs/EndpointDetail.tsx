import { useEffect, useMemo, useState } from 'react';
import { Check, Copy, Loader2, Play } from 'lucide-react';
import { ApiRequestError, sendRawApiRequest, type RawApiResponse } from '../../api';
import { SchemaFields } from './SchemaView';
import {
  buildCurl,
  buildRequestPath,
  classifyStatus,
  exampleFromSchema,
  initialParameterValues,
  isOrgIdName,
  isWriteMethod,
  jsonSchemaOf,
  prettyBody,
  resolveSchema,
  typeLabel,
  validateJson,
  type Endpoint,
  type LiveState,
  type OpenApiDocument,
} from './openapi';

const BODY_DISPLAY_LIMIT = 200000;

const METHOD_CLASS: Record<string, string> = {
  get: 'border-ready-emerald/50 bg-ready-emerald/15',
  post: 'border-outline bg-surface-container-highest',
  put: 'border-drift-amber/50 bg-drift-amber/15',
  patch: 'border-drift-amber/50 bg-drift-amber/15',
  delete: 'border-critical-red/50 bg-critical-red/15',
};

export function MethodBadge({ method }: { method: string }) {
  return (
    <span
      className={`inline-flex w-14 shrink-0 justify-center rounded-md border px-1 py-0.5 font-mono text-[10px] font-bold uppercase text-on-surface ${
        METHOD_CLASS[method.toLowerCase()] ?? 'border-outline-variant bg-surface-container-high'
      }`}
    >
      {method}
    </span>
  );
}

const STATE_DOT: Record<LiveState, string> = {
  up: 'bg-ready-emerald',
  'needs-input': 'bg-drift-amber',
  failing: 'bg-critical-red',
};

const RESULT_WORDS: Record<LiveState, string> = {
  up: 'It worked',
  'needs-input': 'The API did not accept this request',
  failing: 'The API had a problem',
};

export function StateDot({ state }: { state: LiveState }) {
  return <span aria-hidden className={`inline-block h-2 w-2 shrink-0 rounded-full ${STATE_DOT[state]}`} />;
}

const sectionTitle = 'text-[11px] font-bold uppercase tracking-wide text-on-surface-variant';
const fieldClass =
  'w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-2.5 py-1.5 text-sm text-on-surface placeholder:text-on-surface-variant focus:border-ready-emerald focus:outline-none';
const codeBlock =
  'overflow-auto rounded-lg border border-outline-variant bg-surface-container p-3 font-mono text-[11px] leading-relaxed text-on-surface';

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch {
          setCopied(false);
        }
      }}
      className="inline-flex items-center gap-1 rounded-md border border-outline-variant px-2 py-1 text-[11px] font-semibold text-on-surface-variant hover:text-on-surface"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-ready-emerald" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
      {copied ? 'Copied' : label}
    </button>
  );
}

export interface EndpointDetailProps {
  document: OpenApiDocument | null;
  endpoint: Endpoint;
  /** This deployment's API address. Requests never go anywhere else. */
  baseUrl: string;
  orgId: string;
  orgName: string;
  /** True in the demo: requests that change data cannot be sent. */
  writesDisabled: boolean;
}

/** Everything about one endpoint, plus the form that runs it. Mount with `key={endpoint.id}`. */
export function EndpointDetail({ document, endpoint, baseUrl, orgId, orgName, writesDisabled }: EndpointDetailProps) {
  const { operation, method } = endpoint;
  const isWrite = isWriteMethod(method);
  const bodySchema = jsonSchemaOf(operation.requestBody?.content);
  const hasBody = Boolean(operation.requestBody);

  const exampleBody = useMemo(
    () => (hasBody ? JSON.stringify(exampleFromSchema(document, bodySchema, { orgId }) ?? {}, null, 2) : ''),
    [document, bodySchema, hasBody, orgId],
  );

  const [values, setValues] = useState<Record<string, string>>(() => initialParameterValues(document, endpoint, orgId));
  const [bodyText, setBodyText] = useState(exampleBody);
  const [bodyEdited, setBodyEdited] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<RawApiResponse | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  // The organisation can finish loading after this panel opens: fill it in
  // wherever the field is still empty, without overwriting what was typed.
  useEffect(() => {
    if (!orgId) return;
    setValues((current) => {
      let changed = false;
      const next = { ...current };
      for (const parameter of endpoint.parameters) {
        if (isOrgIdName(parameter.name) && !next[parameter.name]) {
          next[parameter.name] = orgId;
          changed = true;
        }
      }
      return changed ? next : current;
    });
  }, [orgId, endpoint]);

  useEffect(() => {
    if (!bodyEdited) setBodyText(exampleBody);
  }, [exampleBody, bodyEdited]);

  const built = buildRequestPath(endpoint, values);
  const bodyError = hasBody ? validateJson(bodyText) : null;
  const sendBody = hasBody && bodyText.trim() !== '' ? bodyText : undefined;
  const organisation = orgName || 'your organisation';
  const visibleParameters = endpoint.parameters.filter((parameter) => parameter.in !== 'header');

  const blockedReason = (() => {
    if (isWrite && writesDisabled) return 'Requests that change data are switched off in the demo.';
    if (built.missing.length > 0) return `Fill in: ${built.missing.join(', ')}.`;
    if (bodyError) return 'Fix the request body first.';
    if (isWrite && !confirmed) return 'Tick the box above to confirm.';
    return null;
  })();
  const canSend = !sending && blockedReason === null;

  const send = async () => {
    if (!canSend) return;
    setSending(true);
    setFailure(null);
    setResult(null);
    try {
      setResult(await sendRawApiRequest(built.path, { method: method.toUpperCase(), body: sendBody }));
    } catch (error) {
      setFailure(error instanceof ApiRequestError ? error.message : 'The request could not be sent.');
    } finally {
      setSending(false);
      // A write must be confirmed again every time.
      setConfirmed(false);
    }
  };

  const curl = buildCurl({ baseUrl, method, path: built.path, body: sendBody });
  const resultState = result ? classifyStatus(result.status) : null;
  const { shownBody, bodyCut } = useMemo(() => {
    if (!result) return { shownBody: '', bodyCut: false };
    const text = result.truncated ? result.bodyText : prettyBody(result.bodyText, result.headers['content-type']);
    const tooLong = text.length > BODY_DISPLAY_LIMIT;
    return {
      shownBody: tooLong ? text.slice(0, BODY_DISPLAY_LIMIT) : text,
      bodyCut: result.truncated || tooLong,
    };
  }, [result]);

  const bodyInputId = `body-${endpoint.id}`.replace(/[^a-zA-Z0-9_-]/g, '_');
  const responses = Object.entries(operation.responses ?? {}).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="min-w-0 space-y-5" data-testid="endpoint-detail">
      <header className="space-y-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <MethodBadge method={method} />
          <code className="min-w-0 break-all font-mono text-sm font-bold text-on-surface">{endpoint.path}</code>
        </div>
        <h3 className="text-lg font-extrabold text-on-surface">{endpoint.summary}</h3>
        {operation.description && (
          <p className="max-w-3xl whitespace-pre-line text-sm text-on-surface-variant">{operation.description}</p>
        )}
        <p className="text-xs text-on-surface-variant">
          {isWrite ? 'This request changes data.' : 'This request only reads data.'}{' '}
          {operation.security && operation.security.length > 0 ? 'It uses your sign-in.' : 'It does not need a sign-in.'}
          {operation.deprecated ? ' It is being retired; avoid building on it.' : ''}
        </p>
      </header>

      <section className="space-y-2">
        <h4 className={sectionTitle}>Parameters</h4>
        {visibleParameters.length === 0 ? (
          <p className="text-xs text-on-surface-variant">This endpoint takes no parameters.</p>
        ) : (
          <ul className="space-y-2">
            {visibleParameters.map((parameter) => {
              const inputId = `param-${endpoint.id}-${parameter.name}`.replace(/[^a-zA-Z0-9_-]/g, '_');
              const required = parameter.required || parameter.in === 'path';
              const description =
                parameter.description ?? resolveSchema(document, parameter.schema).schema.description;
              return (
                <li key={`${parameter.in}-${parameter.name}`} className="grid gap-1.5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] sm:items-start sm:gap-3">
                  <label htmlFor={inputId} className="min-w-0">
                    <span className="flex flex-wrap items-baseline gap-x-2">
                      <code className="break-all font-mono text-xs font-bold text-on-surface">{parameter.name}</code>
                      <span className="text-[11px] text-on-surface-variant">
                        {parameter.in === 'path' ? 'in the address' : 'filter'} · {typeLabel(document, parameter.schema)}
                      </span>
                      {required ? (
                        <span className="rounded border border-outline-variant px-1 text-[10px] font-bold uppercase tracking-wide text-on-surface">
                          Required
                        </span>
                      ) : (
                        <span className="text-[10px] uppercase tracking-wide text-on-surface-variant">Optional</span>
                      )}
                    </span>
                    {description && <span className="mt-0.5 block text-[11px] text-on-surface-variant">{description}</span>}
                  </label>
                  <input
                    id={inputId}
                    type="text"
                    autoComplete="off"
                    spellCheck={false}
                    value={values[parameter.name] ?? ''}
                    onChange={(event) => setValues((current) => ({ ...current, [parameter.name]: event.target.value }))}
                    placeholder={isOrgIdName(parameter.name) ? 'Your organisation id' : required ? 'Required' : 'Leave empty to skip'}
                    className={fieldClass}
                  />
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {hasBody && (
        <section className="space-y-2">
          <h4 className={sectionTitle}>Request body</h4>
          <SchemaFields document={document} schema={bodySchema} />
          <label htmlFor={bodyInputId} className="block text-xs font-semibold text-on-surface">
            What to send (JSON). It starts as an example; change the values you need.
          </label>
          <textarea
            id={bodyInputId}
            value={bodyText}
            onChange={(event) => {
              setBodyEdited(true);
              setBodyText(event.target.value);
            }}
            rows={Math.min(16, Math.max(5, bodyText.split('\n').length + 1))}
            spellCheck={false}
            aria-invalid={Boolean(bodyError)}
            className={`${fieldClass} font-mono text-xs`}
          />
          {bodyError ? (
            <p role="alert" className="text-xs font-semibold text-critical-red">
              This is not valid JSON: {bodyError}
            </p>
          ) : (
            <p className="text-[11px] text-on-surface-variant">The JSON is valid.</p>
          )}
        </section>
      )}

      <section className="space-y-2">
        <h4 className={sectionTitle}>What comes back</h4>
        {responses.length === 0 ? (
          <p className="text-xs text-on-surface-variant">No responses are described for this endpoint.</p>
        ) : (
          <ul className="space-y-1.5">
            {responses.map(([code, response]) => {
              const schema = jsonSchemaOf(response.content);
              const state = classifyStatus(Number(code) || null);
              return (
                <li key={code} className="rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <StateDot state={state} />
                    <span className="font-mono font-bold text-on-surface">{code}</span>
                    <span className="text-on-surface-variant">{response.description || 'No description'}</span>
                  </div>
                  {schema && (
                    <details className="mt-1.5">
                      <summary className="cursor-pointer text-[11px] font-semibold text-on-surface-variant hover:text-on-surface">
                        Show fields and an example
                      </summary>
                      <div className="mt-2 space-y-2">
                        <SchemaFields document={document} schema={schema} />
                        <pre className={`${codeBlock} max-h-64`}>
                          {JSON.stringify(exampleFromSchema(document, schema, { orgId }), null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="space-y-3 rounded-xl border border-outline-variant bg-surface-container-low p-3 sm:p-4" aria-label="Try it">
        <h4 className={sectionTitle}>Try it</h4>

        {isWrite && writesDisabled && (
          <p className="rounded-lg border border-outline-variant bg-surface-container px-3 py-2 text-xs text-on-surface-variant">
            This is the demo, so requests that change data are switched off. You can still run the ones that only
            read, and copy the command below to use in your own account.
          </p>
        )}

        {isWrite && !writesDisabled && (
          <label className="flex items-start gap-2 rounded-lg border border-drift-amber/50 bg-drift-amber/10 px-3 py-2 text-xs text-on-surface">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(event) => setConfirmed(event.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 accent-ready-emerald"
            />
            <span>
              <span className="font-bold">This changes real data in {organisation}.</span> I want to send it.
            </span>
          </label>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={send}
            disabled={!canSend}
            className="inline-flex items-center gap-1.5 rounded-xl bg-on-surface px-4 py-2 text-sm font-bold text-surface-container-lowest hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Play className="h-4 w-4" aria-hidden />}
            {sending ? 'Sending' : 'Send'}
          </button>
          {blockedReason && !sending && <span className="text-xs text-on-surface-variant">{blockedReason}</span>}
        </div>

        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold text-on-surface">The same request as a command</span>
            <CopyButton text={curl} label="Copy" />
          </div>
          <pre className={`${codeBlock} max-h-56 whitespace-pre-wrap break-words`} data-testid="curl-snippet">
            {curl}
          </pre>
          <p className="text-[11px] text-on-surface-variant">
            <code className="font-mono">$RESILAI_TOKEN</code> stands for your sign-in token. It is never shown on
            this page.
          </p>
        </div>

        {failure && (
          <p role="alert" className="rounded-lg border border-critical-red/50 bg-critical-red/10 px-3 py-2 text-xs font-semibold text-on-surface">
            {failure}
          </p>
        )}

        {result && resultState && (
          <div className="space-y-2" data-testid="try-result" aria-live="polite">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
              <span className="inline-flex items-center gap-1.5 font-bold text-on-surface">
                <StateDot state={resultState} />
                Status {result.status}
              </span>
              <span className="text-on-surface-variant">{RESULT_WORDS[resultState]}</span>
              <span className="text-on-surface-variant">{result.durationMs} ms</span>
            </div>
            {Object.keys(result.headers).length > 0 && (
              <dl className="grid gap-x-3 gap-y-0.5 text-[11px] sm:grid-cols-[auto_minmax(0,1fr)]">
                {Object.entries(result.headers).map(([name, value]) => (
                  <div key={name} className="contents">
                    <dt className="font-mono font-bold text-on-surface-variant">{name}</dt>
                    <dd className="break-all font-mono text-on-surface">{value}</dd>
                  </div>
                ))}
              </dl>
            )}
            {shownBody ? (
              <pre className={`${codeBlock} max-h-96`}>{shownBody}</pre>
            ) : (
              <p className="text-xs text-on-surface-variant">The response had no body.</p>
            )}
            {bodyCut && (
              <p className="text-[11px] text-on-surface-variant">
                Long response: showing the first {Math.round(BODY_DISPLAY_LIMIT / 1000)} KB of about{' '}
                {Math.max(1, Math.round(result.bodyLength / 1000))} KB.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default EndpointDetail;
