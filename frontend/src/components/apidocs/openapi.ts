/**
 * Pure helpers for the in-app API explorer: reading an OpenAPI document,
 * resolving references safely, building example payloads and request text.
 * No React and no network in this file.
 */

export type HttpMethod = 'get' | 'post' | 'put' | 'patch' | 'delete' | 'head' | 'options';

export const HTTP_METHODS: HttpMethod[] = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'];

export interface SchemaObject {
  $ref?: string;
  type?: string | string[];
  format?: string;
  title?: string;
  description?: string;
  properties?: Record<string, SchemaObject>;
  required?: string[];
  items?: SchemaObject;
  enum?: unknown[];
  const?: unknown;
  default?: unknown;
  example?: unknown;
  examples?: unknown[];
  anyOf?: SchemaObject[];
  oneOf?: SchemaObject[];
  allOf?: SchemaObject[];
  additionalProperties?: boolean | SchemaObject;
  nullable?: boolean;
  [key: string]: unknown;
}

export interface ParameterObject {
  name: string;
  in: 'path' | 'query' | 'header' | 'cookie';
  required?: boolean;
  description?: string;
  schema?: SchemaObject;
}

export interface MediaTypeObject {
  schema?: SchemaObject;
}

export interface ResponseObject {
  description?: string;
  content?: Record<string, MediaTypeObject>;
}

export interface OperationObject {
  summary?: string;
  description?: string;
  operationId?: string;
  tags?: string[];
  deprecated?: boolean;
  parameters?: ParameterObject[];
  requestBody?: { required?: boolean; content?: Record<string, MediaTypeObject> };
  responses?: Record<string, ResponseObject>;
  security?: unknown[];
}

export interface OpenApiDocument {
  openapi?: string;
  info?: { title?: string; version?: string; description?: string };
  paths?: Record<string, Record<string, unknown>>;
  components?: { schemas?: Record<string, SchemaObject> };
}

export interface Endpoint {
  /** Stable key, e.g. "get /api/v1/connectors". */
  id: string;
  method: HttpMethod;
  path: string;
  tag: string;
  summary: string;
  operation: OperationObject;
  /** Path, query and header parameters (path-level ones merged in). */
  parameters: ParameterObject[];
}

export interface EndpointGroup {
  tag: string;
  label: string;
  endpoints: Endpoint[];
}

const ORG_ID_NAMES = new Set(['org_id', 'organization_id', 'organisation_id', 'orgid']);

/** True for a parameter or field that carries the organisation id. */
export function isOrgIdName(name: string): boolean {
  return ORG_ID_NAMES.has(name.toLowerCase());
}

/** GET and HEAD only read. Everything else can change data. */
export function isWriteMethod(method: string): boolean {
  const upper = method.toUpperCase();
  return upper !== 'GET' && upper !== 'HEAD' && upper !== 'OPTIONS';
}

/** "continuous-scoring" -> "Continuous scoring". */
export function tagLabel(tag: string): string {
  const words = tag.replace(/[-_]+/g, ' ').trim();
  if (!words) return 'Other';
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Flatten the document into a sorted list of endpoints. */
export function listEndpoints(document: OpenApiDocument | null | undefined): Endpoint[] {
  const endpoints: Endpoint[] = [];
  const paths = document?.paths ?? {};
  for (const path of Object.keys(paths)) {
    const item = paths[path] ?? {};
    const shared = Array.isArray(item.parameters) ? (item.parameters as ParameterObject[]) : [];
    for (const method of HTTP_METHODS) {
      const operation = item[method] as OperationObject | undefined;
      if (!operation || typeof operation !== 'object') continue;
      const own = Array.isArray(operation.parameters) ? operation.parameters : [];
      const merged = [...shared.filter((p) => !own.some((o) => o.name === p.name && o.in === p.in)), ...own]
        .filter((p) => p && typeof p.name === 'string' && p.in !== 'cookie');
      endpoints.push({
        id: `${method} ${path}`,
        method,
        path,
        tag: operation.tags?.[0] ?? 'other',
        summary: operation.summary || operation.operationId || path,
        operation,
        parameters: merged,
      });
    }
  }
  return endpoints.sort(
    (a, b) =>
      a.tag.localeCompare(b.tag) ||
      a.path.localeCompare(b.path) ||
      HTTP_METHODS.indexOf(a.method) - HTTP_METHODS.indexOf(b.method),
  );
}

/** Case-insensitive match on path, summary, method and tag. Every word must match. */
export function filterEndpoints(endpoints: Endpoint[], query: string): Endpoint[] {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return endpoints;
  return endpoints.filter((endpoint) => {
    const haystack = `${endpoint.method} ${endpoint.path} ${endpoint.summary} ${endpoint.tag}`.toLowerCase();
    return words.every((word) => haystack.includes(word));
  });
}

export function groupEndpoints(endpoints: Endpoint[]): EndpointGroup[] {
  const groups = new Map<string, EndpointGroup>();
  for (const endpoint of endpoints) {
    let group = groups.get(endpoint.tag);
    if (!group) {
      group = { tag: endpoint.tag, label: tagLabel(endpoint.tag), endpoints: [] };
      groups.set(endpoint.tag, group);
    }
    group.endpoints.push(endpoint);
  }
  return [...groups.values()];
}

// ── References ──────────────────────────────────────────────────────────────

const REF_PREFIX = '#/components/schemas/';

export function refName(ref: string | undefined): string | null {
  return ref && ref.startsWith(REF_PREFIX) ? ref.slice(REF_PREFIX.length) : null;
}

export interface ResolvedSchema {
  schema: SchemaObject;
  /** Names of the references followed to get here. */
  names: string[];
  /** True when the reference pointed back at something already being read. */
  circular: boolean;
}

/**
 * Follow `$ref` until a real schema is reached.
 *
 * `seen` holds the reference names already open higher up; meeting one of them
 * again means the schema contains itself, so the walk stops there.
 */
export function resolveSchema(
  document: OpenApiDocument | null | undefined,
  schema: SchemaObject | undefined,
  seen: ReadonlySet<string> = new Set(),
): ResolvedSchema {
  const names: string[] = [];
  let current: SchemaObject = schema ?? {};
  const visited = new Set(seen);
  for (let hops = 0; hops < 20 && current.$ref; hops += 1) {
    const name = refName(current.$ref);
    if (!name) return { schema: {}, names, circular: false };
    if (visited.has(name)) return { schema: { title: name }, names: [...names, name], circular: true };
    visited.add(name);
    names.push(name);
    current = document?.components?.schemas?.[name] ?? {};
  }
  return { schema: current, names, circular: false };
}

function primaryType(schema: SchemaObject): string | undefined {
  if (Array.isArray(schema.type)) return schema.type.find((t) => t !== 'null') ?? schema.type[0];
  if (schema.type) return schema.type;
  if (schema.properties) return 'object';
  if (schema.items) return 'array';
  return undefined;
}

function isNullOnly(schema: SchemaObject): boolean {
  return schema.type === 'null' || (Array.isArray(schema.type) && schema.type.every((t) => t === 'null'));
}

/** Short human label for a schema: "text", "list of number", "Connector". */
export function typeLabel(
  document: OpenApiDocument | null | undefined,
  schema: SchemaObject | undefined,
  seen: ReadonlySet<string> = new Set(),
  depth = 0,
): string {
  if (!schema) return 'any';
  const resolved = resolveSchema(document, schema, seen);
  const name = resolved.names[resolved.names.length - 1];
  if (resolved.circular || depth > 4) return name ?? 'object';
  const s = resolved.schema;
  const nextSeen = new Set([...seen, ...resolved.names]);

  const variants = s.anyOf ?? s.oneOf;
  if (variants && variants.length > 0) {
    const real = variants.filter((v) => !isNullOnly(v));
    const labels = [...new Set(real.map((v) => typeLabel(document, v, nextSeen, depth + 1)))];
    const joined = labels.join(' or ') || 'any';
    return real.length < variants.length ? `${joined} (optional)` : joined;
  }
  if (s.enum && s.enum.length > 0) {
    const shown = s.enum.slice(0, 6).map((v) => String(v)).join(', ');
    return `one of: ${shown}${s.enum.length > 6 ? ', ...' : ''}`;
  }
  const type = primaryType(s);
  if (type === 'array') return `list of ${typeLabel(document, s.items, nextSeen, depth + 1)}`;
  if (type === 'object' || s.allOf) return name ?? s.title ?? 'object';
  if (type === 'string') {
    if (s.format === 'date-time') return 'date and time';
    if (s.format === 'date') return 'date';
    if (s.format) return `text (${s.format})`;
    return 'text';
  }
  if (type === 'integer') return 'whole number';
  if (type === 'number') return 'number';
  if (type === 'boolean') return 'true or false';
  return name ?? type ?? 'any';
}

// ── Examples ────────────────────────────────────────────────────────────────

export interface ExampleOptions {
  /** Used for any field named like `org_id`. */
  orgId?: string;
}

function stringExample(schema: SchemaObject): string {
  switch (schema.format) {
    case 'date-time':
      return '2026-01-01T09:00:00Z';
    case 'date':
      return '2026-01-01';
    case 'uuid':
      return '00000000-0000-4000-8000-000000000000';
    case 'email':
      return 'name@example.com';
    case 'uri':
    case 'url':
      return 'https://example.com';
    default:
      return 'text';
  }
}

/**
 * Build a sample value that fits the schema. Self-referencing schemas stop at
 * the point where they repeat, and nesting stops after a few levels.
 */
export function exampleFromSchema(
  document: OpenApiDocument | null | undefined,
  schema: SchemaObject | undefined,
  options: ExampleOptions = {},
  seen: ReadonlySet<string> = new Set(),
  depth = 0,
): unknown {
  if (!schema) return null;
  const resolved = resolveSchema(document, schema, seen);
  if (resolved.circular) return null;
  const s = resolved.schema;
  const nextSeen = new Set([...seen, ...resolved.names]);

  if (s.example !== undefined) return s.example;
  if (Array.isArray(s.examples) && s.examples.length > 0) return s.examples[0];
  if (s.default !== undefined && s.default !== null) return s.default;
  if (s.const !== undefined) return s.const;
  if (s.enum && s.enum.length > 0) return s.enum[0];

  if (s.allOf && s.allOf.length > 0) {
    const merged: Record<string, unknown> = {};
    for (const part of s.allOf) {
      const value = exampleFromSchema(document, part, options, nextSeen, depth + 1);
      if (value && typeof value === 'object' && !Array.isArray(value)) Object.assign(merged, value);
    }
    return merged;
  }
  const variants = s.anyOf ?? s.oneOf;
  if (variants && variants.length > 0) {
    const first = variants.find((v) => !isNullOnly(v)) ?? variants[0];
    return exampleFromSchema(document, first, options, nextSeen, depth + 1);
  }

  const type = primaryType(s);
  if (type === 'object') {
    if (depth >= 6) return {};
    const out: Record<string, unknown> = {};
    for (const [name, property] of Object.entries(s.properties ?? {})) {
      out[name] =
        options.orgId && isOrgIdName(name)
          ? options.orgId
          : exampleFromSchema(document, property, options, nextSeen, depth + 1);
    }
    return out;
  }
  if (type === 'array') {
    if (depth >= 6 || !s.items) return [];
    return [exampleFromSchema(document, s.items, options, nextSeen, depth + 1)];
  }
  if (type === 'string') return stringExample(s);
  if (type === 'integer' || type === 'number') return 0;
  if (type === 'boolean') return false;
  return null;
}

/** The JSON body schema of a request or response, if it has one. */
export function jsonSchemaOf(content: Record<string, MediaTypeObject> | undefined): SchemaObject | undefined {
  if (!content) return undefined;
  const key = Object.keys(content).find((k) => k.toLowerCase().includes('json'));
  return key ? content[key]?.schema : undefined;
}

// ── Building a request ──────────────────────────────────────────────────────

export interface BuiltRequest {
  /** Path plus query string, always starting with "/". */
  path: string;
  /** Required parameters that are still empty. */
  missing: string[];
}

/** Fill path parameters and append query parameters from the entered values. */
export function buildRequestPath(endpoint: Endpoint, values: Record<string, string>): BuiltRequest {
  const missing: string[] = [];
  let path = endpoint.path;
  const query: string[] = [];

  for (const parameter of endpoint.parameters) {
    const value = (values[parameter.name] ?? '').trim();
    if (parameter.in === 'path') {
      if (!value) missing.push(parameter.name);
      path = path.replace(`{${parameter.name}}`, value ? encodeURIComponent(value) : `{${parameter.name}}`);
    } else if (parameter.in === 'query') {
      if (value) query.push(`${encodeURIComponent(parameter.name)}=${encodeURIComponent(value)}`);
      else if (parameter.required) missing.push(parameter.name);
    }
  }
  return { path: query.length > 0 ? `${path}?${query.join('&')}` : path, missing };
}

/** Starting values for the parameter fields: defaults, and the active organisation. */
export function initialParameterValues(
  document: OpenApiDocument | null | undefined,
  endpoint: Endpoint,
  orgId: string,
): Record<string, string> {
  const values: Record<string, string> = {};
  for (const parameter of endpoint.parameters) {
    if (parameter.in === 'header') continue;
    if (isOrgIdName(parameter.name) && orgId) {
      values[parameter.name] = orgId;
      continue;
    }
    const fallback = resolveSchema(document, parameter.schema).schema.default;
    values[parameter.name] = fallback === undefined || fallback === null ? '' : String(fallback);
  }
  return values;
}

/** Placeholder shown wherever the sign-in token would go. The real one is never shown. */
export const TOKEN_PLACEHOLDER = '$RESILAI_TOKEN';

export interface CurlInput {
  baseUrl: string;
  method: string;
  path: string;
  body?: string;
}

/** A copyable curl command. The token is always the `$RESILAI_TOKEN` placeholder. */
export function buildCurl({ baseUrl, method, path, body }: CurlInput): string {
  const url = `${baseUrl.replace(/\/+$/, '')}${path}`;
  const lines = [
    `curl -X ${method.toUpperCase()} "${url}"`,
    `  -H "Authorization: Bearer ${TOKEN_PLACEHOLDER}"`,
    '  -H "Accept: application/json"',
  ];
  if (body !== undefined && body.trim() !== '') {
    lines.push('  -H "Content-Type: application/json"');
    lines.push(`  -d '${body.replace(/'/g, `'\\''`)}'`);
  }
  return lines.join(' \\\n');
}

/** Returns an error message for invalid JSON text, or null when it parses. */
export function validateJson(text: string): string | null {
  if (text.trim() === '') return null;
  try {
    JSON.parse(text);
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : 'This is not valid JSON.';
  }
}

/** Pretty-print JSON text; anything else is returned unchanged. */
export function prettyBody(text: string, contentType: string | undefined): string {
  if (!text) return '';
  const looksJson = (contentType ?? '').toLowerCase().includes('json') || /^[\s]*[{[]/.test(text);
  if (!looksJson) return text;
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

// ── Live check ──────────────────────────────────────────────────────────────

export const LIVE_CHECK_LIMIT = 25;

/**
 * GET endpoints the live check never calls by itself, because a "read" there
 * does real work: it contacts the customer's own systems (connector and
 * integration health, Wazuh), fetches from outside services, or builds a
 * document. They stay in the list and can be sent by hand.
 */
export const LIVE_CHECK_SKIP =
  /\/(connectors|integrations)\/[^/]+\/(health|logging-health|agent-status|vulnerabilities)\b|\/reports\/|\.pdf$|\/pdf$|\/intelligence\/latest-versions|\/reference\/openapi$/;
export const LIVE_CHECK_TIMEOUT_MS = 10000;

/**
 * Every endpoint the live check could call without asking for anything: GET,
 * and no required input other than the organisation id.
 */
export function liveCheckEligible(endpoints: Endpoint[]): Endpoint[] {
  return endpoints.filter(
    (endpoint) =>
      endpoint.method === 'get' &&
      !LIVE_CHECK_SKIP.test(endpoint.path) &&
      endpoint.parameters.every(
        (parameter) => !(parameter.required || parameter.in === 'path') || isOrgIdName(parameter.name),
      ),
  );
}

/**
 * The endpoints one live check actually calls. When there are more eligible
 * endpoints than the limit, they are taken in turn from each group so every
 * area of the API is represented, then put back in list order.
 */
export function liveCheckCandidates(endpoints: Endpoint[], limit = LIVE_CHECK_LIMIT): Endpoint[] {
  const eligible = liveCheckEligible(endpoints);
  if (eligible.length <= limit) return eligible;

  const queues = groupEndpoints(eligible).map((group) => [...group.endpoints]);
  const picked = new Set<string>();
  while (picked.size < limit && queues.some((queue) => queue.length > 0)) {
    for (const queue of queues) {
      const next = queue.shift();
      if (next) picked.add(next.id);
      if (picked.size >= limit) break;
    }
  }
  return eligible.filter((endpoint) => picked.has(endpoint.id));
}

export type LiveState = 'up' | 'needs-input' | 'failing';

/** 2xx/3xx: up. 4xx: the API answered but wants something. Anything else: failing. */
export function classifyStatus(status: number | null): LiveState {
  if (status === null) return 'failing';
  if (status >= 200 && status < 400) return 'up';
  if (status >= 400 && status < 500) return 'needs-input';
  return 'failing';
}
