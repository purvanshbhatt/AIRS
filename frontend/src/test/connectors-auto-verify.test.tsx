import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import ConnectorsPage from '../pages/Connectors';
import * as api from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { useCapabilities } from '../hooks/useCapabilities';
import { renderWithRouter } from './utils/test-helpers';

const { addToast } = vi.hoisted(() => ({ addToast: vi.fn() }));

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');
vi.mock('../hooks/useCapabilities');
vi.mock('../components/ui/Toast', () => ({
  useToast: () => ({ toasts: [], addToast, removeToast: vi.fn() }),
}));

const ORG = 'org-connectors-001';
const AWS_NAME = 'Amazon Web Services (AWS)';
const HEALTHY_MESSAGE = 'Connected to AWS account 123456789012. Reading: EC2, IAM. Not enabled: Security Hub, GuardDuty.';
const INVALID_KEYS_MESSAGE = 'AWS rejected the access key or secret. Check for typos or a deactivated key.';

function awsConnector(overrides: Record<string, unknown> = {}) {
  return {
    id: 'conn-aws-1',
    org_id: ORG,
    connector_type: 'aws',
    display_name: AWS_NAME,
    auth_method: 'api_key',
    status: 'pending_auth',
    config: { aws_region: 'us-east-1' },
    sync_interval_minutes: 15,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

function listOf(...connectors: unknown[]) {
  return { connectors, total: connectors.length } as any;
}

function awsCard(): HTMLElement {
  const card = screen.getByRole('heading', { name: AWS_NAME, level: 3 }).closest('div.group');
  if (!card) throw new Error('AWS connector card not found');
  return card as HTMLElement;
}

async function openAwsFormAndSave() {
  await waitFor(() => expect(api.getConnectorsList).toHaveBeenCalled());
  fireEvent.click(within(awsCard()).getByRole('button', { name: /setup/i }));
  fireEvent.change(screen.getByPlaceholderText('AKIA...'), { target: { value: 'AKIAIOSFODNN7EXAMPLE' } });
  fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'example-secret-value' } });
  fireEvent.click(screen.getByRole('button', { name: /save & encrypt connector/i }));
}

describe('Connectors page: a Save is verified straight away', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useActiveOrg).mockReturnValue({
      orgId: ORG,
      orgName: 'Small Clinic',
      org: null,
      orgs: [],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn(),
    } as any);
    vi.mocked(useCapabilities).mockReturnValue({
      capabilities: { status: 'active' },
      loading: false,
      error: null,
      has: () => true,
      isPaid: true,
      isExempt: false,
      plan: 'design-partner',
      refresh: vi.fn(),
    } as any);
    vi.mocked(api.getIntegrationStatus).mockResolvedValue({} as any);
    vi.mocked(api.getEvidenceConfidence).mockResolvedValue({} as any);
    vi.mocked(api.getConnectorsList).mockResolvedValue(listOf());
    vi.mocked(api.createConnector).mockResolvedValue(awsConnector() as any);
    vi.mocked(api.updateConnector).mockResolvedValue(awsConnector() as any);
    vi.mocked(api.checkConnectorHealth).mockResolvedValue({
      status: 'healthy',
      latency_ms: 240,
      message: HEALTHY_MESSAGE,
      checked_at: new Date().toISOString(),
    } as any);
    vi.mocked(api.syncConnectorNow).mockResolvedValue({
      success: true,
      events_ingested: 2,
      errors_count: 0,
      duration_ms: 900,
    } as any);
  });

  it('runs a health check and a first sync after saving a new connector', async () => {
    renderWithRouter(<ConnectorsPage />);
    await openAwsFormAndSave();

    await waitFor(() => expect(api.checkConnectorHealth).toHaveBeenCalledWith('conn-aws-1', ORG));
    await waitFor(() => expect(api.syncConnectorNow).toHaveBeenCalledWith('conn-aws-1', ORG));

    const payload = vi.mocked(api.createConnector).mock.calls[0][0] as any;
    expect(payload.connector_type).toBe('aws');
    expect(payload.auth_method).toBe('api_key');
    expect(payload.credentials.aws_access_key_id).toBe('AKIAIOSFODNN7EXAMPLE');
    expect(payload.credentials.aws_secret_access_key).toBe('example-secret-value');
    // No role ARN is pre-filled, and secrets stay out of the plain config blob.
    expect(payload.credentials.role_arn).toBe('');
    expect(payload.config).not.toHaveProperty('aws_secret_access_key');
    expect(payload.config).not.toHaveProperty('aws_access_key_id');
    expect(payload.config).not.toHaveProperty('aws_session_token');

    expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ message: HEALTHY_MESSAGE, type: 'ready' }));
    expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'First sync complete' }));
    // Reloads the list once the check and sync are done.
    await waitFor(() => expect(api.getConnectorsList).toHaveBeenCalledTimes(2));
  });

  it('shows the real reason and skips the sync when the check fails', async () => {
    vi.mocked(api.checkConnectorHealth).mockResolvedValue({
      status: 'unreachable',
      message: INVALID_KEYS_MESSAGE,
      checked_at: new Date().toISOString(),
    } as any);

    renderWithRouter(<ConnectorsPage />);
    await openAwsFormAndSave();

    await waitFor(() => expect(api.checkConnectorHealth).toHaveBeenCalledWith('conn-aws-1', ORG));
    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ message: INVALID_KEYS_MESSAGE, type: 'error' }))
    );
    expect(api.syncConnectorNow).not.toHaveBeenCalled();
    await waitFor(() => expect(api.getConnectorsList).toHaveBeenCalledTimes(2));
  });

  it('re-checks after updating an existing connector and keeps blank secrets out of the request', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(listOf(awsConnector({ status: 'active' })));

    renderWithRouter(<ConnectorsPage />);
    await waitFor(() => expect(within(awsCard()).getByRole('button', { name: /configure/i })).toBeInTheDocument());
    fireEvent.click(within(awsCard()).getByRole('button', { name: /configure/i }));
    fireEvent.click(screen.getByRole('button', { name: /save & encrypt connector/i }));

    await waitFor(() => expect(api.checkConnectorHealth).toHaveBeenCalledWith('conn-aws-1', ORG));
    expect(api.createConnector).not.toHaveBeenCalled();
    const [id, payload] = vi.mocked(api.updateConnector).mock.calls[0] as any;
    expect(id).toBe('conn-aws-1');
    expect(payload.credentials).not.toHaveProperty('aws_secret_access_key');
    expect(payload.credentials).not.toHaveProperty('aws_access_key_id');
    expect(payload.credentials).not.toHaveProperty('aws_session_token');
  });

  it('labels a saved-but-unchecked connector honestly', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(listOf(awsConnector()));

    renderWithRouter(<ConnectorsPage />);

    await waitFor(() => expect(within(awsCard()).getByText('SAVED, NOT VERIFIED')).toBeInTheDocument());
    expect(screen.getByTestId('connector-last-check-aws')).toHaveTextContent(/has not been checked yet/i);
  });

  it('shows the last check message on the card, in red when the keys were refused', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(
      listOf(
        awsConnector({
          status: 'error',
          config: {
            aws_region: 'us-east-1',
            last_check: {
              status: 'unreachable',
              code: 'INVALID_KEYS',
              message: INVALID_KEYS_MESSAGE,
              checked_at: '2026-11-09T10:00:00+00:00',
              sources: {},
            },
          },
        })
      )
    );

    renderWithRouter(<ConnectorsPage />);

    await waitFor(() => expect(within(awsCard()).getByText('AUTHENTICATION FAILED')).toBeInTheDocument());
    const line = screen.getByTestId('connector-last-check-aws');
    expect(line).toHaveTextContent(INVALID_KEYS_MESSAGE);
    expect(line).toHaveTextContent(/checked/i);
    expect(line.className).toContain('text-critical-red');
  });

  it('shows a degraded check in amber and recommends the SecurityAudit policy in the form', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(
      listOf(
        awsConnector({
          status: 'error',
          config: {
            last_check: {
              status: 'degraded',
              code: 'NO_DATA_SOURCES',
              message: 'Connected to AWS account 123456789012, but nothing can be read yet.',
              checked_at: '2026-11-09T10:00:00+00:00',
            },
          },
        })
      )
    );

    renderWithRouter(<ConnectorsPage />);

    await waitFor(() => expect(within(awsCard()).getByText('DEGRADED')).toBeInTheDocument());
    expect(screen.getByTestId('connector-last-check-aws').className).toContain('text-amber-500');

    fireEvent.click(within(awsCard()).getByRole('button', { name: /setup/i }));
    expect(screen.getByText('SecurityAudit')).toBeInTheDocument();
    expect(screen.getByText('Session token (temporary credentials only)')).toBeInTheDocument();
  });
});
