import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { getApiBaseUrl, sendRawApiRequest, setTokenProvider } from '../api';
import * as authContext from '../contexts/AuthContext';
import * as activeOrgHook from '../hooks/useActiveOrg';
import { ApiExplorer } from '../components/apidocs/ApiExplorer';
import { ApiExplorerLazy } from '../components/apidocs';
import {
  buildCurl,
  exampleFromSchema,
  liveCheckCandidates,
  listEndpoints,
  typeLabel,
  type OpenApiDocument,
} from '../components/apidocs/openapi';
import { renderWithRouter } from './utils/test-helpers';

// The explorer talks to the real API client so these tests can prove the
// sign-in token goes out on the wire but never reaches the page.
vi.mock('../contexts/AuthContext');
vi.mock('../hooks/useActiveOrg');

const SECRET_TOKEN = 'eyJhbGciOi.SECRET-SIGN-IN-TOKEN.zzz';

const mockDocument: OpenApiDocument = {
  openapi: '3.1.0',
  info: { title: 'ResilAI API', version: '1.0.0' },
  paths: {
    '/api/v1/connectors': {
      get: {
        tags: ['connectors'],
        summary: 'List connectors',
        security: [{ HTTPBearer: [] }],
        parameters: [{ name: 'org_id', in: 'query', required: true, schema: { type: 'string' } }],
        responses: {
          '200': {
            description: 'The connected systems',
            content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/Connector' } } } },
          },
        },
      },
      post: {
        tags: ['connectors'],
        summary: 'Add a connector',
        security: [{ HTTPBearer: [] }],
        requestBody: {
          required: true,
          content: { 'application/json': { schema: { $ref: '#/components/schemas/ConnectorCreate' } } },
        },
        responses: { '201': { description: 'Created' }, '422': { description: 'Validation error' } },
      },
    },
    '/api/v1/connectors/{connector_id}': {
      delete: {
        tags: ['connectors'],
        summary: 'Remove a connector',
        parameters: [{ name: 'connector_id', in: 'path', required: true, schema: { type: 'string' } }],
        responses: { '204': { description: 'Removed' } },
      },
      get: {
        tags: ['connectors'],
        summary: 'Get one connector',
        parameters: [{ name: 'connector_id', in: 'path', required: true, schema: { type: 'string' } }],
        responses: { '200': { description: 'The connector' } },
      },
    },
    '/api/v1/technology/stack/{org_id}': {
      get: {
        tags: ['technology'],
        summary: 'Software stack',
        parameters: [
          { name: 'org_id', in: 'path', required: true, schema: { type: 'string' } },
          { name: 'limit', in: 'query', required: false, schema: { type: 'integer', default: 50 } },
        ],
        responses: { '200': { description: 'The software in use' } },
      },
    },
    '/api/v1/methodology': {
      get: { tags: ['methodology'], summary: 'Scoring methodology', responses: { '200': { description: 'ok' } } },
    },
    '/health': {
      get: { tags: ['health'], summary: 'Health check', responses: { '200': { description: 'ok' } } },
    },
  },
  components: {
    schemas: {
      Connector: {
        type: 'object',
        required: ['id'],
        properties: { id: { type: 'string' }, name: { type: 'string' } },
      },
      // Contains itself: the explorer must not loop on it.
      ConnectorCreate: {
        type: 'object',
        required: ['org_id', 'name'],
        properties: {
          org_id: { type: 'string' },
          name: { type: 'string' },
          enabled: { type: 'boolean', default: true },
          parent: { $ref: '#/components/schemas/ConnectorCreate' },
        },
      },
    },
  },
};

const mockStatus = {
  api_version: '1.0.0',
  build: 'abc123',
  environment: 'staging',
  server_time: '2026-11-11T10:00:00+00:00',
  demo_mode: false,
  read_only: false,
  endpoint_count: 7,
  checks: [
    { id: 'api', label: 'API service', ok: true, detail: 'Answering requests.' },
    { id: 'data_store', label: 'Data storage', ok: false, detail: 'Not connected. Saved changes may not be kept.' },
  ],
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', 'x-request-id': 'req-test-1' },
  });
}

let fetchMock: ReturnType<typeof vi.fn>;
/** Per-path status overrides for the live check. */
let statusByPath: Record<string, number>;

function pathOf(input: unknown): string {
  const url = new URL(String(input), 'http://localhost');
  return url.pathname + url.search;
}

function calls(): Array<{ path: string; method: string; headers: Record<string, string>; body?: string }> {
  return fetchMock.mock.calls.map(([input, init]: [unknown, RequestInit]) => ({
    path: pathOf(input),
    method: init?.method ?? 'GET',
    headers: (init?.headers ?? {}) as Record<string, string>,
    body: init?.body as string | undefined,
  }));
}

function signIn(user: unknown = { uid: 'user-1', email: 'manager@riverside.example' }) {
  vi.mocked(authContext.useAuth).mockReturnValue({ user, loading: false } as any);
}

function useOrg(overrides: Partial<activeOrgHook.ActiveOrgState> = {}) {
  vi.mocked(activeOrgHook.useActiveOrg).mockReturnValue({
    orgId: 'org-123',
    orgName: 'Riverside Dental',
    isDemo: false,
    hasOrg: true,
    loading: false,
    org: null,
    orgs: [],
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  } as activeOrgHook.ActiveOrgState);
}

async function renderExplorer() {
  renderWithRouter(<ApiExplorer />);
  const nav = await screen.findByRole('navigation', { name: 'Endpoints' });
  return { nav };
}

function openEndpoint(nav: HTMLElement, method: string, path: string) {
  const button = within(nav)
    .getAllByRole('button')
    .find((b) => b.textContent?.toLowerCase().startsWith(method) && within(b).queryByText(path));
  if (!button) throw new Error(`No ${method} ${path} in the list`);
  fireEvent.click(button);
}

beforeEach(() => {
  statusByPath = {};
  fetchMock = vi.fn(async (input: unknown) => {
    const path = pathOf(input);
    if (path === '/api/v1/reference/openapi') return jsonResponse(mockDocument);
    if (path === '/api/v1/reference/status') return jsonResponse(mockStatus);
    const override = Object.entries(statusByPath).find(([prefix]) => path.startsWith(prefix));
    return jsonResponse({ ok: true, echoed: path }, override ? override[1] : 200);
  });
  vi.stubGlobal('fetch', fetchMock);
  setTokenProvider(async () => SECRET_TOKEN);
  signIn();
  useOrg();
});

afterEach(() => {
  vi.unstubAllGlobals();
  setTokenProvider(async () => null);
});

describe('ApiExplorer: endpoint list', () => {
  it('renders the endpoints from the document, grouped, with methods and a count', async () => {
    const { nav } = await renderExplorer();

    expect(screen.getByTestId('endpoint-count')).toHaveTextContent('7 endpoints');
    for (const group of ['Connectors', 'Technology', 'Methodology', 'Health']) {
      expect(within(nav).getByRole('heading', { name: new RegExp(`^${group}`) })).toBeInTheDocument();
    }
    expect(within(nav).getAllByText('/api/v1/connectors')).toHaveLength(2);
    expect(within(nav).getByText('/api/v1/technology/stack/{org_id}')).toBeInTheDocument();
    expect(within(nav).getByText('Remove a connector')).toBeInTheDocument();

    const methods = within(nav).getAllByRole('button').map((b) => b.textContent?.slice(0, 6).toLowerCase());
    expect(methods.filter((m) => m?.startsWith('get'))).toHaveLength(5);
    expect(methods.filter((m) => m?.startsWith('post'))).toHaveLength(1);
    expect(methods.filter((m) => m?.startsWith('delete'))).toHaveLength(1);

    // The reference is loaded with the user's own session.
    const first = calls()[0];
    expect(first.path).toBe('/api/v1/reference/openapi');
    expect(first.headers.Authorization).toBe(`Bearer ${SECRET_TOKEN}`);
  });

  it('filters the list as the search box is typed in', async () => {
    const { nav } = await renderExplorer();
    const search = screen.getByRole('searchbox', { name: 'Search endpoints' });

    fireEvent.change(search, { target: { value: 'stack' } });
    expect(screen.getByTestId('endpoint-count')).toHaveTextContent('1 of 7 endpoints');
    expect(within(nav).getByText('/api/v1/technology/stack/{org_id}')).toBeInTheDocument();
    expect(within(nav).queryByText('/api/v1/methodology')).not.toBeInTheDocument();

    fireEvent.change(search, { target: { value: 'delete connectors' } });
    expect(screen.getByTestId('endpoint-count')).toHaveTextContent('1 of 7 endpoints');
    expect(within(nav).getByText('Remove a connector')).toBeInTheDocument();

    fireEvent.change(search, { target: { value: 'nothing-like-this' } });
    expect(within(nav).getByText('No endpoint matches that search.')).toBeInTheDocument();

    fireEvent.change(search, { target: { value: '' } });
    expect(screen.getByTestId('endpoint-count')).toHaveTextContent('7 endpoints');
  });

  it('shows parameters, the body example and responses for the chosen endpoint', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'post', '/api/v1/connectors');

    const detail = screen.getByTestId('endpoint-detail');
    expect(within(detail).getByRole('heading', { name: 'Add a connector' })).toBeInTheDocument();
    expect(within(detail).getByText('201')).toBeInTheDocument();
    expect(within(detail).getByText('Validation error')).toBeInTheDocument();

    // Example body is generated from the schema, with the active organisation
    // filled in, and the self-reference does not loop.
    const body = JSON.parse((within(detail).getByRole('textbox', { name: /What to send/ }) as HTMLTextAreaElement).value);
    expect(body).toEqual({ org_id: 'org-123', name: 'text', enabled: true, parent: null });
    expect(within(detail).getAllByText('Required').length).toBeGreaterThanOrEqual(2);
  });
});

describe('ApiExplorer: try it', () => {
  it('sends a read request straight away, to this API only, with the organisation pre-filled', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'get', '/api/v1/technology/stack/{org_id}');
    const detail = screen.getByTestId('endpoint-detail');

    expect((within(detail).getByLabelText(/org_id/) as HTMLInputElement).value).toBe('org-123');
    expect(within(detail).queryByRole('checkbox')).not.toBeInTheDocument();

    const send = within(detail).getByRole('button', { name: 'Send' });
    expect(send).toBeEnabled();
    fireEvent.click(send);

    const result = await within(detail).findByTestId('try-result');
    expect(result).toHaveTextContent('Status 200');
    expect(result).toHaveTextContent(/\d+ ms/);
    expect(result).toHaveTextContent('req-test-1');
    expect(result).toHaveTextContent('application/json');
    expect(result).toHaveTextContent('"echoed": "/api/v1/technology/stack/org-123?limit=50"');

    const sent = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    expect(String(sent[0])).toBe(`${getApiBaseUrl()}/api/v1/technology/stack/org-123?limit=50`);
    expect(sent[1].method).toBe('GET');
  });

  it('requires the confirmation box before every request that changes data', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'post', '/api/v1/connectors');
    const detail = screen.getByTestId('endpoint-detail');

    const send = within(detail).getByRole('button', { name: 'Send' });
    const confirm = within(detail).getByRole('checkbox', { name: /This changes real data in Riverside Dental\./ });
    expect(confirm).not.toBeChecked();
    expect(send).toBeDisabled();

    fireEvent.click(send);
    expect(calls().some((c) => c.method === 'POST')).toBe(false);

    fireEvent.click(confirm);
    expect(send).toBeEnabled();
    fireEvent.click(send);

    await within(detail).findByTestId('try-result');
    const posts = calls().filter((c) => c.method === 'POST');
    expect(posts).toHaveLength(1);
    expect(posts[0].path).toBe('/api/v1/connectors');
    expect(posts[0].headers.Authorization).toBe(`Bearer ${SECRET_TOKEN}`);
    expect(JSON.parse(posts[0].body!)).toMatchObject({ org_id: 'org-123' });

    // The confirmation does not carry over to the next request.
    await waitFor(() => expect(within(detail).getByRole('checkbox')).not.toBeChecked());
    expect(within(detail).getByRole('button', { name: 'Send' })).toBeDisabled();
    fireEvent.click(within(detail).getByRole('button', { name: 'Send' }));
    expect(calls().filter((c) => c.method === 'POST')).toHaveLength(1);
  });

  it('asks for confirmation on DELETE and needs the id filled in', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'delete', '/api/v1/connectors/{connector_id}');
    const detail = screen.getByTestId('endpoint-detail');

    fireEvent.click(within(detail).getByRole('checkbox'));
    expect(within(detail).getByRole('button', { name: 'Send' })).toBeDisabled();
    expect(within(detail).getByText('Fill in: connector_id.')).toBeInTheDocument();

    fireEvent.change(within(detail).getByLabelText(/connector_id/), { target: { value: 'conn 9/x' } });
    expect(within(detail).getByRole('button', { name: 'Send' })).toBeEnabled();
    expect(within(detail).getByTestId('curl-snippet')).toHaveTextContent('/api/v1/connectors/conn%209%2Fx');
  });

  it('blocks sending while the body is not valid JSON', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'post', '/api/v1/connectors');
    const detail = screen.getByTestId('endpoint-detail');

    fireEvent.click(within(detail).getByRole('checkbox'));
    fireEvent.change(within(detail).getByRole('textbox', { name: /What to send/ }), { target: { value: '{ "name": ' } });

    expect(within(detail).getByRole('alert')).toHaveTextContent('This is not valid JSON');
    expect(within(detail).getByRole('button', { name: 'Send' })).toBeDisabled();
  });

  it('switches write requests off in the demo, with an explanation', async () => {
    useOrg({ isDemo: true, orgName: 'Acme Health Systems' });
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'post', '/api/v1/connectors');
    const detail = screen.getByTestId('endpoint-detail');

    expect(within(detail).queryByRole('checkbox')).not.toBeInTheDocument();
    expect(within(detail).getByRole('button', { name: 'Send' })).toBeDisabled();
    expect(within(detail).getByText(/This is the demo, so requests that change data are switched off/)).toBeInTheDocument();

    // Reading still works in the demo.
    openEndpoint(nav, 'get', '/api/v1/methodology');
    expect(within(screen.getByTestId('endpoint-detail')).getByRole('button', { name: 'Send' })).toBeEnabled();
  });

  it('never puts the sign-in token on the page: the curl snippet uses $RESILAI_TOKEN', async () => {
    const { nav } = await renderExplorer();
    openEndpoint(nav, 'post', '/api/v1/connectors');
    let detail = screen.getByTestId('endpoint-detail');

    const curl = within(detail).getByTestId('curl-snippet').textContent ?? '';
    expect(curl).toContain(`curl -X POST "${getApiBaseUrl()}/api/v1/connectors"`);
    expect(curl).toContain('Authorization: Bearer $RESILAI_TOKEN');
    expect(curl).toContain('"org_id": "org-123"');
    expect(curl).not.toContain(SECRET_TOKEN);

    // Copying gives the same placeholder text.
    fireEvent.click(within(detail).getByRole('button', { name: 'Copy' }));
    await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalled());
    const copied = vi.mocked(navigator.clipboard.writeText).mock.calls[0][0];
    expect(copied).toContain('$RESILAI_TOKEN');
    expect(copied).not.toContain(SECRET_TOKEN);

    // Send a write and a read; the token went out on the wire...
    fireEvent.click(within(detail).getByRole('checkbox'));
    fireEvent.click(within(detail).getByRole('button', { name: 'Send' }));
    await within(detail).findByTestId('try-result');
    openEndpoint(nav, 'get', '/api/v1/methodology');
    detail = screen.getByTestId('endpoint-detail');
    fireEvent.click(within(detail).getByRole('button', { name: 'Send' }));
    await within(detail).findByTestId('try-result');
    expect(calls().every((c) => c.headers.Authorization === `Bearer ${SECRET_TOKEN}`)).toBe(true);

    // ...but is nowhere in the DOM, in text or in attributes.
    expect(document.documentElement.outerHTML).not.toContain(SECRET_TOKEN);
    expect(document.documentElement.outerHTML).not.toContain('SECRET-SIGN-IN-TOKEN');
  });
});

describe('ApiExplorer: live check', () => {
  it('reads the API status and pings only read-only endpoints that need nothing but the organisation', async () => {
    statusByPath = { '/api/v1/technology/stack/': 404, '/health': 503 };
    await renderExplorer();

    fireEvent.click(screen.getByRole('button', { name: 'Run live check' }));

    const summary = await screen.findByTestId('live-summary');
    expect(summary).toHaveTextContent('2 working, 1 need input, 1 failing');

    const status = screen.getByTestId('live-status');
    expect(status).toHaveTextContent('staging');
    expect(status).toHaveTextContent('Data storage');
    expect(status).toHaveTextContent('Not connected.');

    const rows = within(screen.getByTestId('live-results')).getAllByRole('listitem');
    const row = (path: string) => rows.find((r) => within(r).queryByText(path))!;
    expect(row('/api/v1/methodology')).toHaveTextContent('Working');
    expect(row('/api/v1/connectors')).toHaveTextContent('Working');
    expect(row('/api/v1/technology/stack/{org_id}')).toHaveTextContent('Needs input');
    expect(row('/api/v1/technology/stack/{org_id}')).toHaveTextContent('404');
    expect(row('/health')).toHaveTextContent('Failing');
    expect(rows).toHaveLength(4);

    const pinged = calls().slice(1);
    expect(pinged.every((c) => c.method === 'GET')).toBe(true);
    expect(pinged.map((c) => c.path)).toEqual([
      '/api/v1/reference/status',
      '/api/v1/connectors?org_id=org-123',
      '/health',
      '/api/v1/methodology',
      '/api/v1/technology/stack/org-123?limit=50',
    ]);
    // Legend is in plain words.
    expect(screen.getByText('The endpoint answered normally.')).toBeInTheDocument();
  });
});

describe('ApiExplorer: signed out', () => {
  it('shows the sign-in notice and the fallback, and calls nothing', async () => {
    signIn(null);
    renderWithRouter(<ApiExplorer signedOutFallback={<p>Static reference stays here</p>} />);

    expect(await screen.findByRole('heading', { name: 'Sign in to try the API from here' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login');
    expect(screen.getByText('Static reference stays here')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Endpoints' })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('treats a 401 from the API as signed out instead of an error', async () => {
    fetchMock.mockImplementation(async () => jsonResponse({ detail: 'Authentication required' }, 401));
    renderWithRouter(<ApiExplorer />);

    expect(await screen.findByRole('heading', { name: 'Sign in to try the API from here' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('offers a retry when the reference cannot be loaded', async () => {
    fetchMock.mockImplementationOnce(async () => jsonResponse({ detail: 'boom' }, 500));
    renderWithRouter(<ApiExplorer />);

    expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded (status 500)');
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('navigation', { name: 'Endpoints' })).toBeInTheDocument();
  });

  it('loads on demand through the lazy export', async () => {
    signIn(null);
    renderWithRouter(<ApiExplorerLazy />);
    expect(await screen.findByRole('heading', { name: 'Sign in to try the API from here' })).toBeInTheDocument();
  });
});

describe('explorer helpers', () => {
  it('builds examples without looping on self-referencing schemas', () => {
    const schema = { $ref: '#/components/schemas/ConnectorCreate' };
    expect(exampleFromSchema(mockDocument, schema, { orgId: 'org-9' })).toEqual({
      org_id: 'org-9',
      name: 'text',
      enabled: true,
      parent: null,
    });
    expect(typeLabel(mockDocument, schema)).toBe('ConnectorCreate');

    const mutual: OpenApiDocument = {
      components: {
        schemas: {
          A: { type: 'object', properties: { b: { $ref: '#/components/schemas/B' } } },
          B: { type: 'object', properties: { a: { type: 'array', items: { $ref: '#/components/schemas/A' } } } },
          Loop: { $ref: '#/components/schemas/Loop' },
        },
      },
    };
    expect(exampleFromSchema(mutual, { $ref: '#/components/schemas/A' })).toEqual({ b: { a: [null] } });
    expect(exampleFromSchema(mutual, { $ref: '#/components/schemas/Loop' })).toBeNull();
    expect(exampleFromSchema(mutual, { $ref: '#/components/schemas/Missing' })).toBeNull();
  });

  it('writes curl with the placeholder token and safe quoting', () => {
    const curl = buildCurl({
      baseUrl: 'https://api.example.test/',
      method: 'post',
      path: '/api/v1/things',
      body: `{"note":"it's fine"}`,
    });
    expect(curl).toContain('curl -X POST "https://api.example.test/api/v1/things"');
    expect(curl).toContain('-H "Authorization: Bearer $RESILAI_TOKEN"');
    expect(curl).toContain(`-d '{"note":"it'\\''s fine"}'`);
    expect(buildCurl({ baseUrl: 'https://api.example.test', method: 'get', path: '/health' })).not.toContain('-d ');
  });

  it('picks live-check candidates: GET only, nothing required but the organisation', () => {
    const picked = liveCheckCandidates(listEndpoints(mockDocument)).map((e) => e.id);
    expect(picked).toEqual([
      'get /api/v1/connectors',
      'get /health',
      'get /api/v1/methodology',
      'get /api/v1/technology/stack/{org_id}',
    ]);
    // Over the limit, picks are spread across the groups rather than taken from the top.
    expect(liveCheckCandidates(listEndpoints(mockDocument), 2).map((e) => e.id)).toEqual([
      'get /api/v1/connectors',
      'get /health',
    ]);
  });

  it('refuses to call anything that is not a path on this API', async () => {
    for (const target of ['https://evil.example/steal', '//evil.example/steal', 'api/v1/x', '/\\evil.example']) {
      await expect(sendRawApiRequest(target)).rejects.toThrow('Only paths on this API can be called.');
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
