import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  getIntegrationStatus, 
  getEvidenceConfidence, 
  getConnectorsList, 
  createConnector, 
  updateConnector,
  checkConnectorHealth, 
  syncConnectorNow, 
  deleteConnector,
  createBillingPortalSession,
} from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { useCapabilities } from '../hooks/useCapabilities';
import { PaywallLockCard } from '../components/common/PaywallLockCard';
import { useToast } from '../components/ui/Toast';
import { 
  Activity, 
  ShieldCheck, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Settings, 
  Plus, 
  X, 
  Server, 
  Key, 
  Zap, 
  Trash2, 
  ExternalLink,
  Shield,
  HelpCircle,
  Database,
  Cloud,
  Layers,
  Lock,
  ArrowRight,
  CreditCard
} from 'lucide-react';

type ConnectorStatus =
  | 'CONNECTED'
  | 'DEGRADED'
  | 'NOT CONFIGURED'
  | 'SAVED, NOT VERIFIED'
  | 'AUTHENTICATION FAILED'
  | 'CONNECTION FAILED'
  | 'NO RECENT EVIDENCE';

/** Outcome of the latest health check / sync, stored by the backend in `config.last_check`. */
interface ConnectorLastCheck {
  status?: string;
  message?: string;
  code?: string | null;
  checked_at?: string;
  sources?: Record<string, string>;
}

// `last_check.code` values that mean the credentials themselves were refused.
const AUTH_FAILURE_CODES = new Set([
  'INVALID_KEYS',
  'EXPIRED_TOKEN',
  'ROLE_NOT_ASSUMABLE',
  'NO_PLATFORM_IDENTITY',
  'PLATFORM_IDENTITY_INVALID',
  'MISSING_CREDENTIALS',
  'INVALID_ROLE_ARN',
]);

const getLastCheck = (connector: any): ConnectorLastCheck | null => {
  const check = connector?.config?.last_check;
  return check && typeof check === 'object' ? (check as ConnectorLastCheck) : null;
};

interface ConnectorCardDef {
  type: string;
  name: string;
  category: string;
  description: string;
  verifies: string[];
  missing: string[];
  icon: string;
  defaultPort?: number;
  configFields: { key: string; label: string; placeholder: string; type?: string; defaultValue?: string; help?: string }[];
}

const CONNECTOR_DEFINITIONS: ConnectorCardDef[] = [
  {
    type: 'splunk',
    name: 'Splunk Enterprise / Cloud (MCP Forwarder)',
    category: 'SIEM & Audit Logging',
    description: 'Ingests real-time authentication logs, EDR coverage, and audit telemetry via Splunk MCP.',
    verifies: ['MFA Enforcement on Admin Accounts (IV-001)', 'EDR Telemetry Coverage (DC-001)', 'SIEM Heartbeat & Audit Persistence (TL-002)'],
    missing: ['Admin MFA Logs', 'Endpoint Agent Feeds', 'Audit Trail Heartbeat'],
    icon: 'analytics',
    configFields: [
      { key: 'mcp_url', label: 'Splunk MCP / Server URL *', placeholder: 'https://splunk-mcp.your-org.com or http://127.0.0.1:9898', defaultValue: 'http://127.0.0.1:9898' },
      { key: 'api_key', label: 'Splunk API Key / Bearer Token *', placeholder: 'resilai_mcp_sec_...', type: 'password' },
      { key: 'sync_interval_minutes', label: 'Sync Interval (Minutes)', placeholder: '15', defaultValue: '15' },
    ],
  },
  {
    type: 'wazuh',
    name: 'Wazuh Open Source XDR',
    category: 'Endpoint Detection & Response',
    description: 'Monitors workstation agent health, vulnerability sweeps, and file integrity telemetry.',
    verifies: ['Workstation Agent Health', 'Vulnerability Scans', 'File Integrity Monitoring'],
    missing: ['Workstation Agent Feeds', 'Vulnerability Sweeps', 'FIM Alerts'],
    icon: 'security',
    defaultPort: 55000,
    configFields: [
      { key: 'host', label: 'Wazuh Manager Host / IP *', placeholder: 'wazuh.internal.clinic.net' },
      { key: 'port', label: 'API Port', placeholder: '55000', defaultValue: '55000' },
      { key: 'api_key', label: 'Wazuh API Key / Basic Auth *', placeholder: 'wazuh-api-secret', type: 'password' },
    ],
  },
  {
    type: 'microsoft',
    name: 'Microsoft 365 / Entra ID',
    category: 'Identity & Access Management',
    description: 'Verifies conditional access policies, user account lifecycle, and MFA enforcement.',
    verifies: ['Active User Directory Sync', 'MFA Enforcement Status', 'Device Compliance State'],
    missing: ['User Directory', 'MFA Enforcement Logs', 'Conditional Access Rules'],
    icon: 'key',
    configFields: [
      { key: 'tenant_id', label: 'Entra / Azure Tenant ID *', placeholder: '72f988bf-86f1-41af-91ab-2d7cd011db47' },
      { key: 'client_id', label: 'Application (Client) ID *', placeholder: '00000000-0000-0000-0000-000000000000' },
      { key: 'client_secret', label: 'Client Secret Value *', placeholder: '••••••••••••••••', type: 'password' },
    ],
  },
  {
    type: 'veeam',
    name: 'Veeam Backup & Replication',
    category: 'Backup & Recovery Assurance',
    description: 'Verifies immutable cloud backup snapshots, recovery SLAs, and ransomware protection.',
    verifies: ['Immutable Cloud Snapshots', 'Air-gapped Storage Lock', 'Recovery Point & Time Objective Verification'],
    missing: ['Backup Immutability Verification', 'Daily Snapshot Logs', 'RTO Telemetry'],
    icon: 'database',
    configFields: [
      { key: 'base_url', label: 'Veeam Enterprise Manager URL *', placeholder: 'https://veeam-em.your-org.com:9398' },
      { key: 'api_key', label: 'API Token / Service Account Key *', placeholder: 'veeam_auth_token_...', type: 'password' },
    ],
  },
  {
    type: 'aws',
    name: 'Amazon Web Services (AWS)',
    category: 'Cloud Infrastructure',
    description: 'Verifies cloud infrastructure logs, IAM permissions, and S3 storage encryption.',
    verifies: ['Storage Bucket Encryption', 'Access Permission Reviews', 'CloudTrail Audit Logs'],
    missing: ['CloudTrail Ingestion', 'S3 Encryption State'],
    icon: 'cloud_done',
    configFields: [
      { key: 'aws_access_key_id', label: 'Access Key ID', placeholder: 'AKIA...' },
      { key: 'aws_secret_access_key', label: 'Secret Access Key', placeholder: '••••••••', type: 'password' },
      { key: 'aws_session_token', label: 'Session token (temporary credentials only)', placeholder: 'Leave blank for a normal IAM user key', type: 'password' },
      { key: 'aws_region', label: 'AWS Region', placeholder: 'us-east-1', defaultValue: 'us-east-1' },
      { key: 'role_arn', label: 'IAM Role ARN (Optional)', placeholder: 'arn:aws:iam::123456789012:role/ResilAIReadOnly', help: 'Only if your workspace has a platform identity. Otherwise leave this blank and use an access key.' },
      { key: 'external_id', label: 'External ID (Optional)', placeholder: 'resilai-org-external-id', help: 'Only used together with a role ARN.' },
    ],
  },
  {
    type: 'duo',
    name: 'Cisco Duo Security',
    category: 'Multi-Factor Authentication',
    description: 'Verifies multi-factor authentication enforcement on VPN and clinical remote access pathways.',
    verifies: ['Authentication Logs', 'Device Posture Hygiene', 'Bypass Code Tracking'],
    missing: ['Duo Admin API Logs', 'Device Hygiene Telemetry'],
    icon: 'phonelink_lock',
    configFields: [
      { key: 'integration_key', label: 'Integration Key (ikey) *', placeholder: 'DIXXXXXXXXXXXXXXXXXX' },
      { key: 'secret_key', label: 'Secret Key (skey) *', placeholder: '••••••••••••••••••••••••••••••••', type: 'password' },
      { key: 'api_hostname', label: 'API Hostname *', placeholder: 'api-XXXXXXXX.duosecurity.com' },
    ],
  },
  {
    type: 'webhook',
    name: 'Custom Webhook / Generic API',
    category: 'MSP & Custom Ingestion',
    description: 'Push verified evidence directly from MSP dashboards, custom monitoring scripts, or CI/CD pipelines.',
    verifies: ['Custom Audit Evidence', 'MSP Telemetry Feeds'],
    missing: ['Custom Event Pipeline'],
    icon: 'api',
    configFields: [
      { key: 'webhook_name', label: 'Integration Name', placeholder: 'My MSP Telemetry Feed', defaultValue: 'Primary MSP Webhook' },
      { key: 'webhook_secret', label: 'Shared Secret *', placeholder: 'Generate a long random string', type: 'password', help: 'Senders must include this value in the X-Webhook-Secret header.' },
    ],
  },
];

// Keys that must only travel in `credentials`, never in the non-secret `config` blob.
const SECRET_CONFIG_KEYS = new Set([
  'api_key',
  'client_secret',
  'secret_key',
  'aws_secret_access_key',
  'aws_access_key_id',
  'aws_session_token',
  'webhook_secret',
]);

const isSecretField = (def: ConnectorCardDef, key: string) =>
  SECRET_CONFIG_KEYS.has(key) || def.configFields.some(f => f.key === key && f.type === 'password');

const PASSWORD_SAVED_PLACEHOLDER = '•••• saved, enter to replace';

// The API returns sync error details as text; older typings describe a list.
const syncErrorText = (details: unknown): string =>
  Array.isArray(details) ? details.join(' ') : typeof details === 'string' ? details : '';

export default function ConnectorsPage() {
  const navigate = useNavigate();
  const { orgId, orgName, isDemo } = useActiveOrg();
  const { has: hasCapability, plan, capabilities, isPaid, isExempt, refresh: refreshCapabilities } = useCapabilities(orgId);
  const { addToast } = useToast();

  // Backend decides: paid plan or admin-exempt account both grant connectors_manage.
  const canManageConnectors = isDemo || hasCapability('connectors_manage');

  // Payment failed but grace period still open — nudge to update the card.
  const isPastDue = !isDemo && capabilities?.status === 'past_due';

  // ---------------------------------------------------------------------------
  // Stripe Checkout return (`?checkout=success`): the webhook that flips the org
  // to paid can land a few seconds after the redirect, so poll capabilities
  // every 2s (max 10 tries) until paid/exempt, then scrub the query params.
  // ---------------------------------------------------------------------------
  const CHECKOUT_POLL_INTERVAL_MS = 2000;
  const CHECKOUT_POLL_MAX = 10;
  const [awaitingCheckout, setAwaitingCheckout] = useState<boolean>(() =>
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('checkout') === 'success'
  );
  const [checkoutPollTick, setCheckoutPollTick] = useState(0);
  const checkoutPollCount = useRef(0);
  const checkoutToastShown = useRef(false);

  const clearCheckoutParams = () => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    params.delete('checkout');
    params.delete('session_id');
    const qs = params.toString();
    window.history.replaceState({}, '', `${window.location.pathname}${qs ? `?${qs}` : ''}${window.location.hash}`);
  };

  useEffect(() => {
    if (!awaitingCheckout) return;
    if (!checkoutToastShown.current) {
      checkoutToastShown.current = true;
      addToast({
        title: 'Payment received',
        message: 'Payment received — unlocking your workspace…',
        type: 'success',
      });
    }
    if (isPaid || isExempt) {
      setAwaitingCheckout(false);
      clearCheckoutParams();
      return;
    }
    if (checkoutPollCount.current >= CHECKOUT_POLL_MAX) {
      setAwaitingCheckout(false);
      clearCheckoutParams();
      addToast({
        title: 'Still activating',
        message: 'Your payment went through, but activation is taking longer than usual. Refresh in a minute or contact support if connectors stay locked.',
        type: 'warning',
      });
      return;
    }
    const timer = setTimeout(async () => {
      checkoutPollCount.current += 1;
      try {
        await refreshCapabilities();
      } finally {
        setCheckoutPollTick((t) => t + 1);
      }
    }, CHECKOUT_POLL_INTERVAL_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [awaitingCheckout, isPaid, isExempt, checkoutPollTick, refreshCapabilities]);

  // Stripe Customer Portal: update card, download invoices, cancel.
  const [openingPortal, setOpeningPortal] = useState(false);
  const handleManageBilling = async () => {
    if (!orgId || openingPortal) return;
    setOpeningPortal(true);
    try {
      const res = await createBillingPortalSession(orgId, window.location.href);
      if (!res?.url) throw new Error('Billing portal returned no URL.');
      window.location.href = res.url;
    } catch (err: any) {
      addToast({
        title: 'Billing portal unavailable',
        message: err?.message || 'Could not open the billing portal. Please contact support.',
        type: 'error',
      });
      setOpeningPortal(false);
    }
  };

  const [loading, setLoading] = useState(true);
  const [confidenceData, setConfidenceData] = useState<any>(null);
  const [integrationStatus, setIntegrationStatus] = useState<any>(null);
  const [registeredConnectors, setRegisteredConnectors] = useState<any[]>([]);

  // Modal State
  const [activeConfigDef, setActiveConfigDef] = useState<ConnectorCardDef | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [healthCheckingId, setHealthCheckingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [modalPaywallError, setModalPaywallError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [integ, conf, connList] = await Promise.all([
        getIntegrationStatus(orgId).catch(() => null),
        getEvidenceConfidence(orgId).catch(() => null),
        getConnectorsList(orgId).catch(() => ({ connectors: [], total: 0 })),
      ]);
      setIntegrationStatus(integ);
      setConfidenceData(conf);
      setRegisteredConnectors(connList?.connectors || []);
    } catch (err) {
      console.warn('[Connectors] Failed to load connector status:', err);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Open configuration modal
  const handleOpenConfig = (def: ConnectorCardDef) => {
    const existing = registeredConnectors.find(c => c.connector_type === def.type);
    const initial: Record<string, string> = {};
    
    def.configFields.forEach(field => {
      if (field.type === 'password') {
        // Secrets are never returned by the backend; leave blank so a saved value is kept unless replaced.
        initial[field.key] = '';
        return;
      }
      initial[field.key] = existing?.config?.[field.key] || field.defaultValue || '';
    });
    
    setFormData(initial);
    setModalPaywallError(null);
    setActiveConfigDef(def);
  };

  // After a Save: check the connection, then pull the first evidence if it works.
  const verifySavedConnector = async (connectorId: string, def: ConnectorCardDef) => {
    setHealthCheckingId(def.type);
    try {
      const health = await checkConnectorHealth(connectorId, orgId);
      const healthy = health.status === 'healthy';
      if (!healthy && health.status !== 'degraded') {
        addToast({
          title: `${def.name} could not connect`,
          message: health.message || 'The connection check failed. Review the details and try again.',
          type: 'error',
        });
        return;
      }
      addToast({
        title: healthy ? `${def.name} is connected` : `${def.name} is connected, but limited`,
        message: health.message || 'The connection works.',
        type: healthy ? 'ready' : 'drift',
      });

      setHealthCheckingId(null);
      setSyncingId(def.type);
      const sync = await syncConnectorNow(connectorId, orgId);
      if (sync.success) {
        addToast({
          title: 'First sync complete',
          message: sync.events_ingested > 0
            ? `Pulled ${sync.events_ingested} record${sync.events_ingested === 1 ? '' : 's'} from ${def.name}.`
            : `${def.name} is connected. There was nothing new to pull yet.`,
          type: 'ready',
        });
      } else {
        addToast({
          title: 'Connected, but the first sync failed',
          message: syncErrorText(sync.error_details) || 'Try "Sync Now" again in a minute.',
          type: 'drift',
        });
      }
    } catch (err: any) {
      addToast({
        title: 'Saved, but the connection could not be checked',
        message: err?.message || 'Use "Test Health" on the connector card to try again.',
        type: 'error',
      });
    } finally {
      setHealthCheckingId(null);
      setSyncingId(null);
    }
  };

  // Submit Connector Configuration
  const handleSaveConnector = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeConfigDef) return;

    setSubmitting(true);
    try {
      if (isDemo) {
        addToast({
          title: 'Demo Environment',
          message: 'Connector configurations are simulated in Sandbox mode. Switch to your live workspace to configure real credentials.',
          type: 'info',
        });
        setActiveConfigDef(null);
        return;
      }

      // Determine auth_method and credentials per connector type
      const connectorType = activeConfigDef.type;
      let authMethod = 'api_key';
      let credentials: Record<string, string> = {};

      switch (connectorType) {
        case 'aws':
          authMethod = formData.role_arn ? 'iam_role' : 'api_key';
          credentials = {
            role_arn: formData.role_arn || '',
            external_id: formData.external_id || '',
            aws_region: formData.aws_region || 'us-east-1',
            aws_access_key_id: formData.aws_access_key_id || '',
            aws_secret_access_key: formData.aws_secret_access_key || '',
            aws_session_token: formData.aws_session_token || '',
          };
          break;
        case 'microsoft':
          authMethod = 'oauth';
          credentials = {
            tenant_id: formData.tenant_id || '',
            client_id: formData.client_id || '',
            client_secret: formData.client_secret || '',
          };
          break;
        case 'duo':
          authMethod = 'api_key';
          credentials = {
            integration_key: formData.integration_key || '',
            secret_key: formData.secret_key || '',
            api_hostname: formData.api_hostname || '',
          };
          break;
        case 'splunk':
          authMethod = 'api_key';
          credentials = {
            api_key: formData.api_key || '',
            mcp_url: formData.mcp_url || '',
            host: formData.host || '',
            port: formData.port || '8089',
          };
          break;
        case 'wazuh':
          authMethod = 'api_key';
          credentials = {
            api_key: formData.api_key || '',
            host: formData.host || formData.manager_host || '',
            manager_host: formData.manager_host || formData.host || '',
            port: formData.port || '55000',
          };
          break;
        case 'veeam':
          authMethod = 'api_key';
          credentials = {
            api_key: formData.api_key || '',
            server_url: formData.server_url || formData.base_url || '',
            base_url: formData.base_url || formData.server_url || '',
          };
          break;
        case 'webhook':
          authMethod = 'webhook';
          credentials = {
            webhook_name: formData.webhook_name || 'Primary MSP Webhook',
            webhook_secret: formData.webhook_secret || '',
          };
          break;
        default:
          // Fallback: collect all form fields as credentials
          authMethod = 'api_key';
          credentials = {
            api_key: formData.api_key || formData.client_secret || formData.secret_key || 'configured',
          };
          break;
      }

      if (!canManageConnectors) {
        const errorMsg = `Connecting live security infrastructure (${activeConfigDef.name}) requires an active ResilAI subscription. Unpaid workspaces can preview connector schemas, but live credential persistence and automated telemetry ingestion are gated.`;
        setModalPaywallError(errorMsg);
        addToast({
          title: 'Subscription Required',
          message: 'An active ResilAI subscription is required to connect live infrastructure.',
          type: 'error',
        });
        return;
      }

      // Secrets go only in `credentials`; strip them from the stored config blob.
      const nonSecretConfig: Record<string, string> = {};
      Object.entries(formData).forEach(([key, value]) => {
        if (!isSecretField(activeConfigDef, key)) nonSecretConfig[key] = value;
      });
      const syncIntervalMinutes = parseInt(formData.sync_interval_minutes || '15', 10);

      // Re-use the existing row for this connector type instead of creating a duplicate per Save.
      const existing = registeredConnectors.find(
        c => c.connector_type === connectorType && c.status !== 'inactive'
      );
      let saved: { id?: string } | null | undefined;

      if (existing) {
        // Blank password fields mean "keep the saved secret"; only send credentials the user re-entered.
        const credentialsToSend: Record<string, string> = {};
        Object.entries(credentials).forEach(([key, value]) => {
          if (!isSecretField(activeConfigDef, key) || value) credentialsToSend[key] = value;
        });
        // A new AWS key replaces the saved session token too: a stale token would break a long-lived key.
        if (connectorType === 'aws' && (credentials.aws_access_key_id || credentials.aws_secret_access_key)) {
          credentialsToSend.aws_session_token = credentials.aws_session_token || '';
        }
        saved = await updateConnector(existing.id, {
          credentials: credentialsToSend,
          config: nonSecretConfig,
          sync_interval_minutes: syncIntervalMinutes,
          display_name: activeConfigDef.name,
        }, orgId);
      } else {
        saved = await createConnector({
          connector_type: connectorType,
          display_name: activeConfigDef.name,
          auth_method: authMethod,
          credentials,
          config: nonSecretConfig,
          sync_interval_minutes: syncIntervalMinutes,
        }, orgId);
      }

      addToast({
        title: existing ? 'Connector Updated' : 'Connector Saved',
        message: `${activeConfigDef.name} is saved and encrypted. Checking the connection now…`,
        type: 'info',
      });

      const savedDef = activeConfigDef;
      setActiveConfigDef(null);
      setModalPaywallError(null);

      // Saving proves nothing: check the connection straight away, then pull the first evidence.
      const savedId = saved?.id || existing?.id;
      if (savedId) await verifySavedConnector(savedId, savedDef);
      await loadData();
    } catch (err: any) {
      console.error('Failed to save connector:', err);
      if (err?.status === 402) {
        const errorMsg = err.message || 'Connecting live telemetry requires an active ResilAI subscription.';
        setModalPaywallError(errorMsg);
        addToast({
          title: 'Subscription Required (HTTP 402)',
          message: errorMsg,
          type: 'error',
        });
        return;
      }
      addToast({
        title: 'Configuration Error',
        message: err.message || 'Failed to save connector configuration.',
        type: 'error',
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Test Health
  const handleTestHealth = async (def: ConnectorCardDef) => {
    const registered = registeredConnectors.find(c => c.connector_type === def.type);
    setHealthCheckingId(def.type);

    try {
      if (isDemo) {
        await new Promise(r => setTimeout(r, 600));
        addToast({
          title: 'Health Check: 200 OK (Simulated)',
          message: `${def.name} connection healthy. Latency: 120ms.`,
          type: 'ready',
        });
        return;
      }

      if (!registered) {
        addToast({
          title: 'Not Configured',
          message: `Please configure ${def.name} before running a health check.`,
          type: 'drift',
        });
        return;
      }

      const res = await checkConnectorHealth(registered.id, orgId);
      addToast({
        title: `Health Check: ${res.status.toUpperCase()}`,
        message: res.message || 'Connected successfully.',
        type: res.status === 'healthy' || res.status === 'active' ? 'ready' : res.status === 'degraded' ? 'drift' : 'error',
      });
      await loadData();
    } catch (err: any) {
      addToast({
        title: 'Health Check Failed',
        message: err.message || 'Connection refused or credentials invalid.',
        type: 'error',
      });
    } finally {
      setHealthCheckingId(null);
    }
  };

  // Manual Sync Telemetry
  const handleSyncTelemetry = async (def: ConnectorCardDef) => {
    const registered = registeredConnectors.find(c => c.connector_type === def.type);
    setSyncingId(def.type);

    try {
      if (isDemo) {
        await new Promise(r => setTimeout(r, 1000));
        addToast({
          title: 'Sync Complete (Simulated)',
          message: `Ingested 3 simulated telemetry events in 85ms. Readiness recomputed.`,
          type: 'ready',
        });
        return;
      }

      if (!registered) {
        addToast({
          title: 'Connector Not Configured',
          message: `Please click Configure to set up ${def.name} first.`,
          type: 'drift',
        });
        return;
      }

      const res = await syncConnectorNow(registered.id, orgId);
      if (res.success) {
        addToast({
          title: 'Telemetry Ingested',
          message: `Ingested ${res.events_ingested} evidence events in ${res.duration_ms}ms. Readiness recalculates on the next scoring run.`,
          type: 'ready',
        });
      } else {
        addToast({
          title: 'Sync Failed',
          message: syncErrorText(res.error_details) || `Sync completed with ${res.errors_count} warnings.`,
          type: 'drift',
        });
      }
      await loadData();
    } catch (err: any) {
      addToast({
        title: 'Sync Failed',
        message: err.message || 'Failed to pull live telemetry.',
        type: 'error',
      });
    } finally {
      setSyncingId(null);
    }
  };

  // Helper to determine status
  const getConnectorStatus = (def: ConnectorCardDef): ConnectorStatus => {
    if (isDemo) {
      if (def.type === 'duo') return 'AUTHENTICATION FAILED';
      return 'CONNECTED';
    }

    const registered = registeredConnectors.find(c => c.connector_type === def.type);
    if (registered && (registered.status === 'active' || registered.status === 'healthy')) {
      return 'CONNECTED';
    }

    if (def.type === 'splunk' && (integrationStatus?.splunk_status === 'configured' || integrationStatus?.splunk_status === 'connected')) {
      return 'CONNECTED';
    }
    if (def.type === 'wazuh' && (integrationStatus?.wazuh_status === 'configured' || integrationStatus?.wazuh_status === 'connected')) {
      return 'CONNECTED';
    }

    // Saved but never checked: do not let it pass for "not configured" (or for working).
    if (registered?.status === 'pending_auth') return 'SAVED, NOT VERIFIED';
    if (registered?.status === 'error') {
      const lastCheck = getLastCheck(registered);
      if (lastCheck?.status === 'degraded') return 'DEGRADED';
      return lastCheck?.code && AUTH_FAILURE_CODES.has(lastCheck.code) ? 'AUTHENTICATION FAILED' : 'CONNECTION FAILED';
    }

    return 'NOT CONFIGURED';
  };

  const getStatusBadge = (status: ConnectorStatus) => {
    switch (status) {
      case 'CONNECTED':
        return 'bg-ready-emerald/15 text-ready-emerald border-ready-emerald/30';
      case 'AUTHENTICATION FAILED':
      case 'CONNECTION FAILED':
        return 'bg-critical-red/15 text-critical-red border-critical-red/30';
      case 'DEGRADED':
      case 'SAVED, NOT VERIFIED':
        return 'bg-amber-500/15 text-amber-500 border-amber-500/30';
      case 'NOT CONFIGURED':
      default:
        return 'bg-surface-container-high text-on-surface-variant border-outline-variant/30';
    }
  };

  const activeCount = CONNECTOR_DEFINITIONS.filter(d => getConnectorStatus(d) === 'CONNECTED').length;
  const hasLiveConnector = registeredConnectors.some(c => c.status === 'active' || c.status === 'syncing');

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Past-due billing warning (grace period) */}
      {isPastDue && (
        <div
          role="alert"
          className="p-4 bg-amber-500/10 border border-amber-500/40 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-sm"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-on-surface">Your last payment failed.</p>
              <p className="text-on-surface-variant text-xs mt-0.5">
                Access continues for a short grace period — update your card to keep connectors running.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleManageBilling}
            disabled={openingPortal}
            className="px-4 py-2 bg-amber-500 text-slate-950 rounded-xl hover:brightness-110 font-semibold text-xs transition-all flex items-center justify-center gap-1.5 shadow-sm shrink-0 disabled:opacity-50"
          >
            <CreditCard className="w-4 h-4" />
            <span>{openingPortal ? 'Opening…' : 'Manage billing'}</span>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/40 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">
              Telemetry Connectors
            </h1>
            {isDemo ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase bg-amber-500/20 text-amber-500 border border-amber-500/30">
                SIMULATED TELEMETRY
              </span>
            ) : hasLiveConnector ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30">
                LIVE PRODUCTION
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase bg-surface-container-high text-on-surface-variant border border-outline-variant/40">
                NO CONNECTORS YET
              </span>
            )}
          </div>
          <p className="text-sm text-on-surface-variant max-w-2xl">
            Live telemetry integrations that provide cryptographic evidence to mathematically verify your incident readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3.5 py-1.5 rounded-full bg-surface-container border border-outline-variant/40 text-xs font-mono font-medium text-on-surface flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${activeCount > 0 ? 'bg-ready-emerald animate-pulse' : 'bg-on-surface-variant/40'}`} />
            <strong>{activeCount}</strong> / {CONNECTOR_DEFINITIONS.length} Active
          </span>
          {isPaid && !isDemo && (
            <button
              type="button"
              onClick={handleManageBilling}
              disabled={openingPortal}
              className="px-3.5 py-2 bg-surface-container border border-outline-variant/40 text-on-surface rounded-xl hover:bg-surface-container-high font-semibold text-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <CreditCard className="w-4 h-4" />
              <span>{openingPortal ? 'Opening…' : 'Manage billing'}</span>
            </button>
          )}
          <button 
            onClick={() => handleOpenConfig(CONNECTOR_DEFINITIONS[0])}
            className="px-4 py-2 bg-ready-emerald text-on-primary-container rounded-xl hover:brightness-110 font-semibold text-xs transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Connect Splunk / SIEM</span>
          </button>
        </div>
      </div>

      {/* Paywall Gate Notice for Unpaid Organizations */}
      {!canManageConnectors && (
        <PaywallLockCard
          feature="Live Telemetry Connector Management"
          description="Connecting live security infrastructure (Splunk, Wazuh, Microsoft 365, AWS, Veeam) requires an active ResilAI subscription. Unpaid workspaces can preview connector schemas and evidence mappings, but live credential persistence and automated telemetry ingestion are gated."
          requiredPlan="design-partner"
          currentPlan={plan}
          onUpgrade={() => navigate('/pricing')}
        />
      )}

      {/* Demo Mode Educational Notice */}
      {isDemo && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-on-surface">You are currently exploring in Sandbox Demo Mode</p>
              <p className="text-on-surface-variant mt-0.5">
                The connector states below are populated with illustrative clinic telemetry. To connect your organization&apos;s real Splunk or Wazuh instance, sign in to your live workspace.
              </p>
            </div>
          </div>
          <a
            href="/login"
            className="px-4 py-2 bg-amber-500 text-white font-semibold rounded-xl shrink-0 hover:bg-amber-600 transition-colors text-center"
          >
            Sign In to Real Workspace
          </a>
        </div>
      )}

      {/* Verification Confidence Banner */}
      <div className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-on-surface">Overall Telemetry Confidence</h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              {activeCount === 0 && !isDemo ? (
                <span className="text-amber-500 font-medium">No active telemetry feeds. Connect your systems below to begin automated control verification.</span>
              ) : (
                <span>Direct telemetry feeds verify {confidenceData?.overall_confidence_pct ?? (isDemo ? 98 : 0)}% of all organizational security controls.</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-surface-container px-4 py-2.5 rounded-xl border border-outline-variant/30 shrink-0">
          <span className="text-xs font-mono text-on-surface-variant">Data Freshness:</span>
          <span className="text-xs font-mono text-ready-emerald font-bold">
            {activeCount > 0 || isDemo ? 'Real-time (< 15m)' : 'No Feed'}
          </span>
        </div>
      </div>

      {/* Connectors Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {CONNECTOR_DEFINITIONS.map((def) => {
          const status = getConnectorStatus(def);
          const isConnected = status === 'CONNECTED';
          const registered = registeredConnectors.find(c => c.connector_type === def.type);
          const lastCheck = isDemo ? null : getLastCheck(registered);
          const lastCheckTone = lastCheck?.status === 'healthy'
            ? 'text-on-surface-variant'
            : lastCheck?.status === 'degraded'
              ? 'text-amber-500'
              : 'text-critical-red';

          return (
            <div 
              key={def.type} 
              className="bg-surface-container-low rounded-2xl border border-surface-bright p-6 flex flex-col justify-between hover:border-ready-emerald/40 transition-all shadow-sm group"
            >
              <div>
                {/* Top Row: Icon, Title, Status */}
                <div className="flex justify-between items-start mb-4 gap-2">
                  <div className="flex items-start gap-3">
                    <div className={`w-11 h-11 rounded-xl border flex items-center justify-center shrink-0 ${
                      isConnected ? 'bg-ready-emerald/10 border-ready-emerald/30 text-ready-emerald' : 'bg-surface-container border-outline-variant/40 text-on-surface-variant'
                    }`}>
                      <span className="material-symbols-outlined text-2xl" data-icon={def.icon}>
                        {def.icon}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-on-surface">{def.name}</h3>
                      </div>
                      <span className="text-[11px] font-mono text-on-surface-variant uppercase tracking-wider block">
                        {def.category}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1.5 shrink-0">
                    <span className={`px-2.5 py-1 rounded-full text-[11px] font-mono uppercase font-bold border shrink-0 ${getStatusBadge(status)}`}>
                      {status}
                    </span>
                    {!isConnected && !canManageConnectors && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        Plan Required
                      </span>
                    )}
                  </div>
                </div>

                {/* Why the connector is (not) working, from the latest check */}
                {lastCheck?.message ? (
                  <p
                    className={`text-[11px] leading-relaxed mb-3 ${lastCheckTone}`}
                    data-testid={`connector-last-check-${def.type}`}
                  >
                    {lastCheck.message}
                    {lastCheck.checked_at && (
                      <span className="font-mono text-on-surface-variant">
                        {' '}· checked {new Date(lastCheck.checked_at).toLocaleString()}
                      </span>
                    )}
                  </p>
                ) : registered?.status === 'pending_auth' && !isDemo ? (
                  <p className="text-[11px] leading-relaxed mb-3 text-amber-500" data-testid={`connector-last-check-${def.type}`}>
                    Saved, but the connection has not been checked yet. Click Test Health.
                  </p>
                ) : null}

                <p className="text-xs text-on-surface-variant leading-relaxed mb-4">
                  {def.description}
                </p>

                {/* Evidence Capabilities */}
                <div className="space-y-3 p-3.5 bg-surface-container rounded-xl border border-surface-bright mb-4">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-on-surface-variant uppercase tracking-wider block mb-1">
                      Controls Verified by this Feed:
                    </span>
                    <ul className="space-y-1">
                      {def.verifies.map((v, i) => (
                        <li key={i} className="text-xs text-on-surface flex items-center gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-ready-emerald shrink-0" />
                          <span className="truncate">{v}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {!isConnected && def.missing.length > 0 && (
                    <div className="pt-2 border-t border-outline-variant/20">
                      <span className="text-[10px] font-mono font-bold text-amber-500 uppercase tracking-wider block mb-1">
                        Current Visibility Gap:
                      </span>
                      <ul className="space-y-1">
                        {def.missing.map((m, i) => (
                          <li key={i} className="text-xs text-on-surface-variant flex items-center gap-2">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                            <span className="truncate">{m}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Action Row */}
              <div className="pt-4 border-t border-surface-bright flex flex-wrap items-center justify-between gap-3">
                <span className="text-[11px] font-mono text-on-surface-variant">
                  {isConnected 
                    ? (isDemo ? 'Last Sync: 2m ago' : `Last Sync: ${registered?.last_sync_at ? new Date(registered.last_sync_at).toLocaleTimeString() : 'Recent'}`)
                    : 'Last Sync: Never'}
                </span>

                <div className="flex items-center gap-2">
                  {/* Test Health Button */}
                  <button
                    onClick={() => handleTestHealth(def)}
                    disabled={healthCheckingId === def.type}
                    className="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    title="Probe external connection"
                  >
                    <Zap className={`w-3.5 h-3.5 ${healthCheckingId === def.type ? 'animate-spin text-amber-500' : 'text-ready-emerald'}`} />
                    <span>{healthCheckingId === def.type ? 'Checking...' : 'Test Health'}</span>
                  </button>

                  {/* Manual Sync Button */}
                  <button
                    onClick={() => handleSyncTelemetry(def)}
                    disabled={syncingId === def.type}
                    className="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    title="Pull latest evidence"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${syncingId === def.type ? 'animate-spin text-ready-emerald' : 'text-on-surface-variant'}`} />
                    <span>{syncingId === def.type ? 'Syncing...' : 'Sync Now'}</span>
                  </button>

                  {/* Configure / Edit Button */}
                  <button
                    onClick={() => handleOpenConfig(def)}
                    className="px-3.5 py-1.5 rounded-lg bg-ready-emerald/15 hover:bg-ready-emerald hover:text-on-primary-container text-ready-emerald border border-ready-emerald/30 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                  >
                    <Settings className="w-3.5 h-3.5" />
                    <span>{isConnected ? 'Configure' : 'Setup'}</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Connector Configuration Modal */}
      {activeConfigDef && (
        <div 
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={(e) => {
            if (e.target === e.currentTarget) setActiveConfigDef(null);
          }}
        >
          <div 
            className="bg-surface-container-low rounded-2xl max-w-xl w-full max-h-[90vh] flex flex-col border border-outline-variant/40 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-container shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-ready-emerald/15 border border-ready-emerald/30 text-ready-emerald flex items-center justify-center">
                  <span className="material-symbols-outlined text-xl" data-icon={activeConfigDef.icon}>
                    {activeConfigDef.icon}
                  </span>
                </div>
                <div>
                  <h2 className="text-base font-bold text-on-surface">{activeConfigDef.name}</h2>
                  <p className="text-xs text-on-surface-variant font-mono">{activeConfigDef.category}</p>
                </div>
              </div>
              <button 
                onClick={() => setActiveConfigDef(null)}
                className="p-1.5 hover:bg-surface-container-highest rounded-full text-on-surface-variant hover:text-on-surface transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSaveConnector} className="p-6 space-y-4 overflow-y-auto flex-1 text-on-surface">
              {isDemo && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-600 dark:text-amber-400 text-xs">
                  <strong>Sandbox Notice:</strong> Form inputs will simulate registration. Live credentials must be saved inside a real customer organization.
                </div>
              )}

              {/* Paywall Banner for Unpaid Workspaces */}
              {!canManageConnectors && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-600 dark:text-amber-400 shrink-0 mt-0.5">
                      <Lock className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-on-surface">Active Subscription Required</h4>
                      <p className="text-xs text-on-surface-variant mt-0.5 leading-relaxed">
                        Connecting live security infrastructure ({activeConfigDef.name}) requires an active ResilAI subscription. Unpaid workspaces can preview connector schemas and evidence mappings, but live credential persistence and automated telemetry ingestion are gated.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-1 pl-11">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveConfigDef(null);
                        navigate('/pricing');
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-xs rounded-xl hover:shadow-md hover:shadow-primary-500/20 active:scale-[0.98] transition-all flex items-center gap-1.5 shadow-sm"
                    >
                      <span>Go to Subscription & Pricing</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}

              {/* Inline Paywall Error Notice */}
              {modalPaywallError && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl space-y-3 animate-in fade-in duration-200">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0 mt-0.5">
                      <AlertCircle className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-rose-600 dark:text-rose-400">Subscription Required</h4>
                      <p className="text-xs text-on-surface-variant mt-0.5 leading-relaxed">
                        {modalPaywallError}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-1 pl-11">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveConfigDef(null);
                        navigate('/pricing');
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-xs rounded-xl hover:shadow-md transition-all flex items-center gap-1.5 shadow-sm"
                    >
                      <span>View Subscription Plans</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}

              <p className="text-xs text-on-surface-variant leading-relaxed">
                Credentials are encrypted using AES-256-GCM at rest and never exposed to the frontend or narrative engine.
              </p>

              {activeConfigDef.type === 'aws' && (
                <div className="p-3 bg-surface-container rounded-xl border border-surface-bright space-y-1.5 text-xs text-on-surface-variant leading-relaxed">
                  <p>
                    <strong className="text-on-surface">Recommended:</strong> create a read-only IAM user, attach the AWS-managed{' '}
                    <code className="font-mono text-on-surface">SecurityAudit</code> policy, and paste its access key below.
                  </p>
                  <p>
                    Use a role ARN only if your workspace has a platform identity. Security Hub is optional: without it we still read your servers, databases and user accounts.
                  </p>
                </div>
              )}

              {activeConfigDef.configFields.map((field) => (
                <div key={field.key} className="space-y-1">
                  <label className="block text-xs font-semibold text-on-surface">
                    {field.label}
                  </label>
                  <input
                    type={field.type || 'text'}
                    value={formData[field.key] || ''}
                    onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                    placeholder={
                      field.type === 'password' && field.key !== 'aws_session_token' && registeredConnectors.some(c => c.connector_type === activeConfigDef.type)
                        ? PASSWORD_SAVED_PLACEHOLDER
                        : field.placeholder
                    }
                    required={
                      field.label.includes('*') &&
                      !(field.type === 'password' && registeredConnectors.some(c => c.connector_type === activeConfigDef.type))
                    }
                    className="w-full bg-surface-container text-xs text-on-surface rounded-xl px-3.5 py-2.5 border border-outline-variant/40 focus:outline-none focus:ring-2 focus:ring-ready-emerald/50 font-mono"
                  />
                  {field.help && (
                    <p className="text-[10px] text-on-surface-variant">{field.help}</p>
                  )}
                </div>
              ))}

              {activeConfigDef.type === 'webhook' && (
                <div className="p-3 bg-surface-container rounded-xl border border-surface-bright space-y-2 text-xs">
                  <span className="font-mono text-ready-emerald font-bold block">Webhook Endpoint URL:</span>
                  <div className="p-2 bg-surface-container-high rounded font-mono text-[11px] select-all break-all text-on-surface">
                    {`${import.meta.env.VITE_API_BASE_URL || window.location.origin}/api/v1/connectors/webhook/webhook?org_id=${orgId || 'your-org-id'}`}
                  </div>
                  <p className="text-[11px] text-on-surface-variant">
                    POST JSON to this URL with header <code className="font-mono text-on-surface">X-Webhook-Secret</code> set to the Shared Secret above.
                  </p>
                </div>
              )}

              <div className="pt-4 border-t border-outline-variant/30 flex flex-wrap items-center justify-between gap-3">
                {!canManageConnectors ? (
                  <button
                    type="button"
                    onClick={() => {
                      setActiveConfigDef(null);
                      navigate('/pricing');
                    }}
                    className="px-3 py-2 text-xs font-bold text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1.5"
                  >
                    <span>View Subscription Plans</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <div />
                )}

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setActiveConfigDef(null)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-on-surface-variant hover:bg-surface-container"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 bg-ready-emerald text-on-primary-container rounded-xl text-xs font-bold hover:brightness-110 transition-all shadow-sm disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {submitting ? 'Saving & Encrypting...' : 'Save & Encrypt Connector'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
