import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  checkHealth,
  getApiBaseUrl,
  toggleOrgAnalytics,
  getOrganizationProfile,
  updateOrganizationProfile,
  getApplicableFrameworks,
  ApiRequestError,
  createBillingPortalSession,
  createApiKey,
  listApiKeys,
  revokeApiKey,
  createWebhook,
  listWebhooks,
  deleteWebhook,
  testWebhook,
  generateAuditorLink,
  listAuditorLinks,
  revokeAuditorLink,
} from '../api';
import { usePreferences, resetPreferences, START_PAGE_OPTIONS } from '../lib/preferences';
import type { MapViewPreference } from '../lib/preferences';
import { clearAllLocalData, getLocalDataSummary } from '../lib/userData';
import { useAuth } from '../contexts/AuthContext';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { ThemeContext } from '../contexts/ThemeContext';
import { useToast } from '../components/ui/Toast';
import {
  Settings as SettingsIcon,
  Server,
  Code2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Database,
  User,
  Mail,
  Shield,
  Plug,
  Eye,
  EyeOff,
  Activity,
  CreditCard,
  Cpu,
  ShieldCheck,
  Building,
  Globe,
  Loader2,
  ExternalLink,
  BookOpen,
  Sun,
  Moon,
  Laptop,
  ChevronRight,
  ArrowRight,
  Terminal,
  Key,
  Lock,
  Sparkles,
  LogOut,
  Copy,
  Plus,
  Send,
  Share2,
  Clock,
  Check,
  SlidersHorizontal,
} from 'lucide-react';
import { ApiExplorerLazy } from '../components/apidocs';
import type { OrganizationProfile, ApplicableFramework, OrganizationProfileUpdate } from '../types';

interface HealthStatus {
  status: 'checking' | 'ok' | 'error';
  message?: string;
  latencyMs?: number;
  lastChecked?: Date;
}

type SettingsTab = 'workspace' | 'frameworks' | 'apikeys' | 'webhooks' | 'preferences' | 'api' | 'diagnostics';

interface ApiKeyItem {
  id: string;
  /** Sandbox samples only: the server stores no label for a key. */
  name?: string;
  prefix: string;
  token?: string;
  scope: string;
  createdAt: string;
  /** Sandbox samples only. */
  lastUsed?: string;
  /** Live: `last_used_at` from the server (null until the key is first used). */
  lastUsedAt?: string | null;
  isActive: boolean;
}

interface WebhookItem {
  id: string;
  url: string;
  /** Sandbox samples only: the server stores no description for a webhook. */
  description?: string;
  events: string[];
  status: 'active' | 'paused';
  createdAt: string;
}

interface AuditorLinkItem {
  id: string;
  /** Sandbox samples only: the server stores no auditor name. */
  auditorOrg?: string;
  /** Live: held in memory only for links created in this session (the server never lists tokens). */
  token?: string;
  expiresAt: string;
  /** Sandbox samples only. */
  scope?: string;
  createdAt: string;
  /** Live: `created_by` and `access_count` from the server. */
  createdBy?: string;
  accessCount?: number;
}

interface LoadState {
  status: 'idle' | 'loading' | 'ready' | 'error';
  error?: string;
}

const IDLE: LoadState = { status: 'idle' };

/** Shown on the tab and in every toast when the sandbox simulates a change. */
const DEMO_NOTICE = 'Sample data: nothing is created in the demo.';

/** Older builds kept invented rows under these names. Nothing reads them any more. */
const LEGACY_SETTINGS_STORAGE_KEYS = [
  'resilai_settings_api_keys',
  'resilai_settings_webhooks',
  'resilai_settings_auditor_links',
];

/** The scopes the server accepts (ALLOWED_SCOPES in app/schemas/integrations.py). */
const LIVE_API_KEY_SCOPES: Array<{ value: string; label: string }> = [
  { value: 'scores:read', label: 'scores:read (Read readiness scores)' },
  { value: 'scores:write', label: 'scores:write (Write readiness scores)' },
  { value: 'findings:read', label: 'findings:read (Read findings)' },
  { value: 'findings:write', label: 'findings:write (Write findings)' },
  { value: 'reports:read', label: 'reports:read (Read reports)' },
  { value: 'webhooks:read', label: 'webhooks:read (Read webhooks)' },
  { value: 'webhooks:write', label: 'webhooks:write (Manage webhooks)' },
];

/** The only event the server sends to webhooks today. */
const LIVE_WEBHOOK_EVENTS = ['assessment.scored'];

const MAP_VIEW_OPTIONS: Array<{ value: MapViewPreference; label: string; hint: string }> = [
  { value: 'auto', label: 'Automatic', hint: '3D on wide screens, 2D on phones.' },
  { value: '3d', label: '3D', hint: 'Always open the 3D map.' },
  { value: '2d', label: '2D', hint: 'Always open the flat map.' },
];

function sampleApiKeys(): ApiKeyItem[] {
  return [
    {
      id: 'key-1',
      name: 'M365 Telemetry Ingestion Agent',
      prefix: 'resilai_live_9f2a',
      scope: 'telemetry:write',
      createdAt: new Date(Date.now() - 14 * 86400000).toISOString(),
      lastUsed: '12 minutes ago',
      isActive: true,
    },
    {
      id: 'key-2',
      name: 'Veeam WORM Backup Sentinel',
      prefix: 'resilai_live_4b8c',
      scope: 'telemetry:write',
      createdAt: new Date(Date.now() - 30 * 86400000).toISOString(),
      lastUsed: 'Just now',
      isActive: true,
    },
    {
      id: 'key-3',
      name: 'Executive Reporting Dashboard API',
      prefix: 'resilai_read_1e7d',
      scope: 'scores:read',
      createdAt: new Date(Date.now() - 60 * 86400000).toISOString(),
      lastUsed: '2 hours ago',
      isActive: true,
    },
  ];
}

function sampleWebhooks(): WebhookItem[] {
  return [
    {
      id: 'wh-1',
      url: 'https://siem.acme-health.org/api/v1/resilai-drift-sink',
      description: 'Splunk SIEM Critical Readiness Drift Ingestion',
      events: ['score.drift', 'immutability.lost'],
      status: 'active',
      createdAt: new Date(Date.now() - 10 * 86400000).toISOString(),
    },
    {
      id: 'wh-2',
      url: 'https://hooks.slack.com/services/T00/B00/X00EXAMPLE',
      description: 'Security & Operations On-Call Alerts',
      events: ['agent.violation', 'incident.declared'],
      status: 'active',
      createdAt: new Date(Date.now() - 25 * 86400000).toISOString(),
    },
  ];
}

function sampleAuditorLinks(): AuditorLinkItem[] {
  return [
    {
      id: 'aud-1',
      auditorOrg: 'Coalfire SOC 2 Audit Team',
      token: 'aud_soc2_live_891e4a2',
      expiresAt: new Date(Date.now() + 14 * 86400000).toISOString(),
      scope: 'Read-only Cryptographic Evidence Ledger',
      createdAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    },
    {
      id: 'aud-2',
      auditorOrg: 'Travelers Cyber Underwriting Risk Assessment',
      token: 'aud_underwriter_772bf10',
      expiresAt: new Date(Date.now() + 5 * 86400000).toISOString(),
      scope: 'Veeam Backup Immutability & MFA Enforcement',
      createdAt: new Date(Date.now() - 5 * 86400000).toISOString(),
    },
  ];
}

/**
 * The server's own words for a failed request. A plan refusal (402, or a 403
 * that is not the read-only demo guard) is prefixed so it reads as a plan
 * limit, and keeps whatever detail the API returned.
 */
function describeApiError(err: unknown, feature: string): string {
  const e = (err && typeof err === 'object' ? err : {}) as {
    message?: unknown;
    status?: unknown;
    code?: unknown;
    detail?: unknown;
  };
  const message =
    typeof e.message === 'string' && e.message.trim() ? e.message.trim() : 'The server did not say why the request failed.';
  const planRefusal =
    e.status === 402 || e.code === 'PAYMENT_REQUIRED' || (e.status === 403 && !/read-only/i.test(message));
  if (!planRefusal) return message;

  let currentPlan = '';
  if (typeof e.detail === 'string') {
    try {
      const parsed = JSON.parse(e.detail) as { current_plan?: unknown };
      if (parsed && parsed.current_plan) currentPlan = ` Current plan: ${String(parsed.current_plan)}.`;
    } catch {
      // detail was not JSON; the message already carries what the server said
    }
  }
  return `Your plan does not include ${feature}. ${message}${currentPlan}`;
}

function formatDate(value?: string | null): string {
  if (!value) return '';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString();
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('workspace');
  const [health, setHealth] = useState<HealthStatus>({ status: 'checking' });
  const [localDataSummary, setLocalDataSummary] = useState<{ key: string; size: number }[]>([]);
  const [clearingData, setClearingData] = useState(false);
  const [analyticsUpdating, setAnalyticsUpdating] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState<boolean>(
    () => localStorage.getItem('airs_analytics_enabled') !== 'false'
  );

  // Framework Profiles State
  const [profile, setProfile] = useState<OrganizationProfile | null>(null);
  const [frameworks, setFrameworks] = useState<ApplicableFramework[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [updatingProfile, setUpdatingProfile] = useState<string | null>(null);

  const apiBaseUrl = getApiBaseUrl();
  const { user, signOut } = useAuth();
  const { orgId: activeOrgId, orgName, orgs, isDemo, tier, selectOrg } = useActiveOrg();
  const themeContext = useContext(ThemeContext);
  const { addToast } = useToast();
  const [prefs, setPrefs] = usePreferences();

  const effectiveOrgId = activeOrgId || (orgs.length > 0 ? orgs[0].id : null);

  // A live workspace reads and writes API keys, webhooks and auditor links on
  // the server only. The sandbox keeps sample rows in memory and never stores them.
  const liveOrgId = !isDemo && activeOrgId ? activeOrgId : null;
  const liveOrgRef = useRef<string | null>(liveOrgId);
  liveOrgRef.current = liveOrgId;

  // API Keys State
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>(() => (isDemo ? sampleApiKeys() : []));
  const [apiKeysLoad, setApiKeysLoad] = useState<LoadState>(IDLE);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScope, setNewKeyScope] = useState(isDemo ? 'telemetry:write' : 'scores:read');
  const [generatedSecret, setGeneratedSecret] = useState<string | null>(null);

  // Webhooks State
  const [webhooks, setWebhooks] = useState<WebhookItem[]>(() => (isDemo ? sampleWebhooks() : []));
  const [webhooksLoad, setWebhooksLoad] = useState<LoadState>(IDLE);
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [newWebhookUrl, setNewWebhookUrl] = useState('');
  const [newWebhookDesc, setNewWebhookDesc] = useState('');
  const [newWebhookSecret, setNewWebhookSecret] = useState('');

  // Auditor Share Links State
  const [auditorLinks, setAuditorLinks] = useState<AuditorLinkItem[]>(() => (isDemo ? sampleAuditorLinks() : []));
  const [auditorLoad, setAuditorLoad] = useState<LoadState>(IDLE);
  const [showAuditorModal, setShowAuditorModal] = useState(false);
  const [auditorOrgName, setAuditorOrgName] = useState('');
  const [auditorExpiryDays, setAuditorExpiryDays] = useState(14);
  const [generatedAuditorUrl, setGeneratedAuditorUrl] = useState<string | null>(null);
  // Tokens of links created in this session, keyed by `expires_at`. Memory only.
  const sessionAuditorTokens = useRef<Record<string, string>>({});

  // Shared by the three live sections
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<{ apikeys?: string; webhooks?: string; auditor?: string }>({});

  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadApiKeys = useCallback(async (orgId: string) => {
    setApiKeysLoad({ status: 'loading' });
    try {
      const rows = await listApiKeys(orgId);
      if (liveOrgRef.current !== orgId) return;
      setApiKeys(
        (rows || []).map((row) => ({
          id: row.id,
          prefix: row.prefix,
          scope: (row.scopes || []).join(', '),
          createdAt: row.created_at,
          lastUsedAt: row.last_used_at ?? null,
          isActive: row.is_active,
        }))
      );
      setApiKeysLoad({ status: 'ready' });
    } catch (err) {
      if (liveOrgRef.current !== orgId) return;
      setApiKeysLoad({ status: 'error', error: describeApiError(err, 'API keys') });
    }
  }, []);

  const loadWebhooks = useCallback(async (orgId: string) => {
    setWebhooksLoad({ status: 'loading' });
    try {
      const rows = await listWebhooks(orgId);
      if (liveOrgRef.current !== orgId) return;
      // The server keeps a deleted webhook as an inactive row; it no longer receives events.
      setWebhooks(
        (rows || [])
          .filter((row) => row.is_active)
          .map((row) => ({
            id: row.id,
            url: row.url,
            events: row.event_types || [],
            status: 'active' as const,
            createdAt: row.created_at,
          }))
      );
      setWebhooksLoad({ status: 'ready' });
    } catch (err) {
      if (liveOrgRef.current !== orgId) return;
      setWebhooksLoad({ status: 'error', error: describeApiError(err, 'webhooks') });
    }
  }, []);

  const loadAuditorLinks = useCallback(async (orgId: string) => {
    setAuditorLoad({ status: 'loading' });
    try {
      const res = await listAuditorLinks(orgId);
      if (liveOrgRef.current !== orgId) return;
      setAuditorLinks(
        (res?.active_links || []).map((row, index) => ({
          id: `${row.created_at}-${index}`,
          token: sessionAuditorTokens.current[row.expires_at],
          expiresAt: row.expires_at,
          createdAt: row.created_at,
          createdBy: row.created_by,
          accessCount: row.access_count,
        }))
      );
      setAuditorLoad({ status: 'ready' });
    } catch (err) {
      if (liveOrgRef.current !== orgId) return;
      setAuditorLoad({ status: 'error', error: describeApiError(err, 'auditor links') });
    }
  }, []);

  // Start again whenever the workspace changes (another organisation, or sandbox <-> live).
  useEffect(() => {
    sessionAuditorTokens.current = {};
    setApiKeys(isDemo ? sampleApiKeys() : []);
    setWebhooks(isDemo ? sampleWebhooks() : []);
    setAuditorLinks(isDemo ? sampleAuditorLinks() : []);
    setApiKeysLoad(IDLE);
    setWebhooksLoad(IDLE);
    setAuditorLoad(IDLE);
    setShowKeyModal(false);
    setShowWebhookModal(false);
    setShowAuditorModal(false);
    setGeneratedSecret(null);
    setGeneratedAuditorUrl(null);
    setModalError(null);
    setActionError({});
    setNewKeyScope(isDemo ? 'telemetry:write' : 'scores:read');
    if (!isDemo) {
      try {
        LEGACY_SETTINGS_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
      } catch {
        // storage can be unavailable in private windows
      }
    }
  }, [isDemo, liveOrgId]);

  // Live: read from the server the first time a tab is opened.
  useEffect(() => {
    if (!liveOrgId) return;
    if (activeTab === 'apikeys' && apiKeysLoad.status === 'idle') void loadApiKeys(liveOrgId);
    if (activeTab === 'webhooks') {
      if (webhooksLoad.status === 'idle') void loadWebhooks(liveOrgId);
      if (auditorLoad.status === 'idle') void loadAuditorLinks(liveOrgId);
    }
  }, [activeTab, liveOrgId, apiKeysLoad.status, webhooksLoad.status, auditorLoad.status, loadApiKeys, loadWebhooks, loadAuditorLinks]);

  const copyToClipboard = (text: string, id: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    addToast({
      title: 'Copied to Clipboard',
      message: `${label} copied successfully.`,
      type: 'ready',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  // A secret or link is shown once: it leaves memory when its dialog closes.
  const closeKeyModal = () => {
    setShowKeyModal(false);
    setGeneratedSecret(null);
  };

  const closeAuditorModal = () => {
    setShowAuditorModal(false);
    setGeneratedAuditorUrl(null);
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isDemo) {
      // Sandbox only: a made-up sample row, kept in memory. No key exists on any server.
      if (!newKeyName.trim()) return;
      const randomHex = Array.from({ length: 24 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
      const fullSecret = `resilai_sample_${randomHex}`;
      const prefix = `resilai_sample_${randomHex.slice(0, 4)}••••`;

      const newKey: ApiKeyItem = {
        id: `key-${Date.now()}`,
        name: newKeyName.trim(),
        prefix,
        token: fullSecret,
        scope: newKeyScope,
        createdAt: new Date().toISOString(),
        lastUsed: 'Never',
        isActive: true,
      };

      setApiKeys((prev) => [newKey, ...prev]);
      setGeneratedSecret(fullSecret);
      setNewKeyName('');
      addToast({
        title: 'Sample API Key Added',
        message: `${DEMO_NOTICE} This key does not work.`,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    const orgId = liveOrgId;
    setSaving(true);
    setModalError(null);
    try {
      const created = await createApiKey(orgId, [newKeyScope]);
      if (liveOrgRef.current !== orgId) return;
      // The only copy of the secret is the one the server returned.
      setGeneratedSecret(created.api_key);
      addToast({
        title: 'API Key Created',
        message: 'Copy the key now. The server will not show it again.',
        type: 'ready',
      });
      void loadApiKeys(orgId);
    } catch (err) {
      setModalError(describeApiError(err, 'API keys'));
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeApiKey = async (keyId: string) => {
    if (isDemo) {
      setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
      addToast({
        title: 'Sample Key Removed',
        message: DEMO_NOTICE,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    if (!window.confirm('Revoke this API key? Anything that uses it will stop working. This cannot be undone.')) return;
    const orgId = liveOrgId;
    setBusyId(keyId);
    setActionError((prev) => ({ ...prev, apikeys: undefined }));
    try {
      await revokeApiKey(keyId);
      addToast({
        title: 'API Key Revoked',
        message: 'The server no longer accepts this key.',
        type: 'info',
      });
      if (liveOrgRef.current === orgId) void loadApiKeys(orgId);
    } catch (err) {
      const message = describeApiError(err, 'API keys');
      setActionError((prev) => ({ ...prev, apikeys: message }));
      addToast({ title: 'Could Not Revoke Key', message, type: 'error' });
    } finally {
      setBusyId(null);
    }
  };

  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWebhookUrl.trim()) return;

    if (isDemo) {
      const newWh: WebhookItem = {
        id: `wh-${Date.now()}`,
        url: newWebhookUrl.trim(),
        description: newWebhookDesc.trim() || 'Custom Outbound SIEM Destination',
        events: ['score.drift', 'agent.violation'],
        status: 'active',
        createdAt: new Date().toISOString(),
      };

      setWebhooks((prev) => [newWh, ...prev]);
      setNewWebhookUrl('');
      setNewWebhookDesc('');
      setShowWebhookModal(false);
      addToast({
        title: 'Sample Webhook Added',
        message: `${DEMO_NOTICE} No request was sent.`,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    const orgId = liveOrgId;
    setSaving(true);
    setModalError(null);
    try {
      await createWebhook(orgId, {
        url: newWebhookUrl.trim(),
        event_types: LIVE_WEBHOOK_EVENTS,
        secret: newWebhookSecret.trim() || undefined,
      });
      if (liveOrgRef.current !== orgId) return;
      setNewWebhookUrl('');
      setNewWebhookSecret('');
      setShowWebhookModal(false);
      addToast({
        title: 'Webhook Registered',
        message: 'Use Test Ping to check that it can be reached.',
        type: 'ready',
      });
      void loadWebhooks(orgId);
    } catch (err) {
      setModalError(describeApiError(err, 'webhooks'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteWebhook = async (whId: string) => {
    if (isDemo) {
      setWebhooks((prev) => prev.filter((w) => w.id !== whId));
      addToast({
        title: 'Sample Webhook Removed',
        message: DEMO_NOTICE,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    if (!window.confirm('Delete this webhook? ResilAI will stop sending events to it.')) return;
    const orgId = liveOrgId;
    setBusyId(whId);
    setActionError((prev) => ({ ...prev, webhooks: undefined }));
    try {
      await deleteWebhook(whId);
      addToast({
        title: 'Webhook Removed',
        message: 'ResilAI no longer sends events to this address.',
        type: 'info',
      });
      if (liveOrgRef.current === orgId) void loadWebhooks(orgId);
    } catch (err) {
      const message = describeApiError(err, 'webhooks');
      setActionError((prev) => ({ ...prev, webhooks: message }));
      addToast({ title: 'Could Not Delete Webhook', message, type: 'error' });
    } finally {
      setBusyId(null);
    }
  };

  const handleTestWebhook = async (whId: string) => {
    if (isDemo) {
      addToast({
        title: 'Sample Test Ping',
        message: `${DEMO_NOTICE} No request was sent.`,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    setBusyId(`test-${whId}`);
    setActionError((prev) => ({ ...prev, webhooks: undefined }));
    try {
      const result = await testWebhook(whId);
      if (result.delivered) {
        addToast({
          title: 'Test Ping Delivered',
          message: result.status_code ? `The endpoint answered HTTP ${result.status_code}.` : 'The endpoint accepted the test event.',
          type: 'ready',
        });
      } else {
        const reason = result.error || (result.status_code ? `The endpoint answered HTTP ${result.status_code}.` : 'The endpoint did not answer.');
        setActionError((prev) => ({ ...prev, webhooks: `Test ping was not delivered. ${reason}` }));
        addToast({ title: 'Test Ping Not Delivered', message: reason, type: 'error' });
      }
    } catch (err) {
      const message = describeApiError(err, 'webhooks');
      setActionError((prev) => ({ ...prev, webhooks: message }));
      addToast({ title: 'Test Ping Failed', message, type: 'error' });
    } finally {
      setBusyId(null);
    }
  };

  const handleCreateAuditorLink = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isDemo) {
      if (!auditorOrgName.trim()) return;
      const randomHash = Math.random().toString(36).substring(2, 10);
      const newLink: AuditorLinkItem = {
        id: `aud-${Date.now()}`,
        auditorOrg: auditorOrgName.trim(),
        token: `aud_sample_${randomHash}`,
        expiresAt: new Date(Date.now() + auditorExpiryDays * 86400000).toISOString(),
        scope: 'Read-only Cryptographic Evidence Ledger',
        createdAt: new Date().toISOString(),
      };

      setAuditorLinks((prev) => [newLink, ...prev]);
      setAuditorOrgName('');
      setShowAuditorModal(false);
      addToast({
        title: 'Sample Auditor Link Added',
        message: `${DEMO_NOTICE} This link does not open anything.`,
        type: 'info',
      });
      return;
    }

    if (!liveOrgId) return;
    const orgId = liveOrgId;
    setSaving(true);
    setModalError(null);
    try {
      const created = await generateAuditorLink(orgId, auditorExpiryDays * 24);
      if (liveOrgRef.current !== orgId) return;
      sessionAuditorTokens.current[created.expires_at] = created.token;
      setGeneratedAuditorUrl(`${window.location.origin}/auditor?token=${encodeURIComponent(created.token)}`);
      addToast({
        title: 'Auditor Link Created',
        message: `Read-only. Expires ${formatDate(created.expires_at)}. Copy the link now: it is shown once.`,
        type: 'ready',
      });
      void loadAuditorLinks(orgId);
    } catch (err) {
      setModalError(describeApiError(err, 'auditor links'));
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeAuditorLink = async (link: AuditorLinkItem) => {
    if (isDemo) {
      setAuditorLinks((prev) => prev.filter((l) => l.id !== link.id));
      addToast({
        title: 'Sample Auditor Link Removed',
        message: DEMO_NOTICE,
        type: 'info',
      });
      return;
    }

    // The server identifies a link by its token, which it never lists.
    if (!liveOrgId || !link.token) return;
    if (!window.confirm('Revoke this auditor link? Whoever holds it will lose access straight away.')) return;
    const orgId = liveOrgId;
    setBusyId(link.id);
    setActionError((prev) => ({ ...prev, auditor: undefined }));
    try {
      await revokeAuditorLink(orgId, link.token);
      delete sessionAuditorTokens.current[link.expiresAt];
      addToast({
        title: 'Auditor Access Revoked',
        message: 'The link no longer opens the read-only view.',
        type: 'info',
      });
      if (liveOrgRef.current === orgId) void loadAuditorLinks(orgId);
    } catch (err) {
      const message = describeApiError(err, 'auditor links');
      setActionError((prev) => ({ ...prev, auditor: message }));
      addToast({ title: 'Could Not Revoke Link', message, type: 'error' });
    } finally {
      setBusyId(null);
    }
  };

  const checkApiHealth = async () => {
    setHealth({ status: 'checking' });
    const startTime = performance.now();
    try {
      const result = await checkHealth();
      const latencyMs = Math.round(performance.now() - startTime);
      setHealth({
        status: result.status === 'ok' ? 'ok' : 'error',
        message: result.status === 'ok' ? 'API service is fully operational' : `Unexpected status: ${result.status}`,
        latencyMs,
        lastChecked: new Date(),
      });
    } catch (err) {
      setHealth({
        status: 'error',
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : (err instanceof Error ? err.message : 'Unknown connection error'),
        lastChecked: new Date(),
      });
    }
  };

  const refreshLocalDataSummary = () => {
    setLocalDataSummary(getLocalDataSummary());
  };

  const handleClearLocalData = () => {
    setClearingData(true);
    clearAllLocalData();
    refreshLocalDataSummary();
    addToast({
      title: 'Cache Flushed',
      message: 'Local browser session cache and draft states cleared.',
      type: 'info',
    });
    setTimeout(() => setClearingData(false), 500);
  };

  const handleAnalyticsToggle = async (enabled: boolean) => {
    setAnalyticsEnabled(enabled);
    localStorage.setItem('airs_analytics_enabled', enabled ? 'true' : 'false');
    if (effectiveOrgId) {
      setAnalyticsUpdating(true);
      try {
        await toggleOrgAnalytics(effectiveOrgId, enabled);
        addToast({
          title: 'Telemetry Updated',
          message: enabled ? 'Telemetry logging enabled.' : 'Telemetry logging disabled.',
          type: 'ready',
        });
      } catch {
        // Non-critical
      } finally {
        setAnalyticsUpdating(false);
      }
    }
  };

  const loadOrgData = async (targetOrgId: string) => {
    setLoadingProfile(true);
    try {
      const [profileData, fwData] = await Promise.all([
        getOrganizationProfile(targetOrgId),
        getApplicableFrameworks(targetOrgId),
      ]);
      setProfile(profileData);
      setFrameworks(fwData.frameworks || []);
    } catch {
      // Handle offline or error gracefully
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleProfileToggle = async (key: keyof OrganizationProfileUpdate, value: boolean) => {
    if (!effectiveOrgId || !profile) return;
    setUpdatingProfile(key as string);

    // Regions are chosen on their own below; a data toggle never changes them.
    const updatePayload: OrganizationProfileUpdate = { [key]: value };

    try {
      const updated = await updateOrganizationProfile(effectiveOrgId, updatePayload);
      setProfile(updated);
      const fwData = await getApplicableFrameworks(effectiveOrgId);
      setFrameworks(fwData.frameworks || []);
      addToast({
        title: 'Framework Scope Updated',
        message: 'Compliance obligations recalculated deterministically.',
        type: 'ready',
      });
    } catch {
      addToast({
        title: 'Update Notice',
        message: 'Could not sync framework profile with backend server.',
        type: 'error',
      });
    } finally {
      setUpdatingProfile(null);
    }
  };

  /** Add or remove one region the organisation operates in, then recalculate. */
  const handleRegionToggle = async (code: string) => {
    if (!effectiveOrgId || !profile) return;
    const current = profile.geo_regions || [];
    const next = current.includes(code) ? current.filter((r) => r !== code) : [...current, code];
    setUpdatingProfile(`region-${code}`);
    try {
      const updated = await updateOrganizationProfile(effectiveOrgId, { geo_regions: next });
      setProfile(updated);
      const fwData = await getApplicableFrameworks(effectiveOrgId);
      setFrameworks(fwData.frameworks || []);
    } catch {
      addToast({
        title: 'Update Notice',
        message: 'Could not save the region. Nothing was changed.',
        type: 'error',
      });
    } finally {
      setUpdatingProfile(null);
    }
  };

  const handleOpenBillingPortal = async () => {
    if (!effectiveOrgId) return;
    try {
      const res = await createBillingPortalSession(effectiveOrgId, window.location.href);
      if (res.url) {
        window.location.href = res.url;
      }
    } catch (err: any) {
      addToast({
        title: 'Billing Portal',
        message: err.message || 'Customer portal requires an active subscription.',
        type: 'info',
      });
    }
  };

  useEffect(() => {
    checkApiHealth();
    refreshLocalDataSummary();
    if (effectiveOrgId) {
      loadOrgData(effectiveOrgId);
    }
  }, [effectiveOrgId]);

  const OPERATING_REGIONS = [
    { code: 'US', label: 'United States' },
    { code: 'EU', label: 'European Union' },
    { code: 'UK', label: 'United Kingdom' },
    { code: 'AE', label: 'UAE' },
    { code: 'SA', label: 'Saudi Arabia' },
    { code: 'QA', label: 'Qatar' },
    { code: 'BH', label: 'Bahrain' },
    { code: 'KW', label: 'Kuwait' },
    { code: 'OM', label: 'Oman' },
    { code: 'IN', label: 'India' },
    { code: 'CA', label: 'Canada' },
    { code: 'AU', label: 'Australia' },
    { code: 'SG', label: 'Singapore' },
  ];

  const profileConfigs = [
    {
      key: 'processes_phi' as const,
      title: 'HIPAA Health Data (PHI)',
      category: 'Healthcare & Clinical',
      description: 'Protects patient health information, clinical databases, EHR systems, and Business Associate agreements.',
      icon: Activity,
      color: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
    },
    {
      key: 'uses_ai_in_production' as const,
      title: 'AI in Use (NIST AI RMF, EU AI Act)',
      category: 'AI & Autonomous Agents',
      description: 'You use AI systems in your work. Adds NIST AI RMF, and the EU AI Act when you pick the European Union below.',
      icon: Cpu,
      color: 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20',
    },
    {
      key: 'processes_cardholder_data' as const,
      title: 'PCI-DSS Payment Security',
      category: 'Financial & Transactions',
      description: 'Enforces standards for cardholder data isolation, encrypted token storage, and network perimeter validation.',
      icon: CreditCard,
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      key: 'processes_pii' as const,
      title: 'Personal Data (Privacy Laws)',
      category: 'Privacy & Data Rights',
      description: 'Personal data of patients, clients or staff. Adds the privacy law of each region you pick below: GDPR in the EU, UK GDPR, or the data protection law of each Gulf state.',
      icon: Globe,
      color: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20',
    },
    {
      key: 'financial_services' as const,
      title: 'NIST CSF 2.0 & FFIEC',
      category: 'Banking & Critical Infrastructure',
      description: 'Continuous cyber readiness and business continuity requirements expected for financial and critical systems.',
      icon: Building,
      color: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
    },
    {
      key: 'handles_dod_data' as const,
      title: 'Defense Contract (CMMC)',
      category: 'Government & Defense',
      description: 'Triggers NIST SP 800-171 controls required for handling Controlled Unclassified Information (CUI).',
      icon: ShieldCheck,
      color: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    },
    {
      key: 'government_contractor' as const,
      title: 'Federal Contractor (FedRAMP)',
      category: 'Government & Defense',
      description: 'Toggles advisory constraints for cloud systems and SaaS platforms hosting public sector and federal workloads.',
      icon: Shield,
      color: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    },
  ];

  // Counts come from the sandbox samples, or from the server once it has answered. Never a guess.
  const apiKeysBadge = isDemo
    ? apiKeys.length
    : apiKeysLoad.status === 'ready'
      ? apiKeys.filter((k) => k.isActive).length
      : undefined;
  const webhooksBadge = isDemo
    ? webhooks.length + auditorLinks.length
    : webhooksLoad.status === 'ready' && auditorLoad.status === 'ready'
      ? webhooks.length + auditorLinks.length
      : undefined;

  const demoNotice = (
    <div
      role="note"
      className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300"
    >
      <span className="font-bold">{DEMO_NOTICE}</span> The rows below are examples, and Add, Test and Revoke are simulated in this browser.
    </div>
  );

  const renderSectionError = (message: string | undefined, onRetry?: () => void) =>
    message ? (
      <div
        role="alert"
        className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-600 dark:text-rose-400 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
      >
        <span className="break-words">{message}</span>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="self-start sm:self-center px-3 py-1.5 text-xs font-semibold bg-surface-container-high hover:bg-surface-bright text-on-surface border border-outline-variant/60 rounded-xl transition-colors cursor-pointer"
          >
            Try again
          </button>
        )}
      </div>
    ) : null;

  const renderListState = (load: LoadState, count: number, emptyText: string) => {
    if (isDemo) return null;
    if (!liveOrgId) {
      return (
        <div className="p-6 text-center rounded-xl bg-surface-container border border-dashed border-outline-variant text-xs text-on-surface-variant">
          Select or create an organisation first.
        </div>
      );
    }
    if (count > 0 || load.status === 'error') return null;
    if (load.status === 'ready') {
      return (
        <div className="p-6 text-center rounded-xl bg-surface-container border border-dashed border-outline-variant text-xs text-on-surface-variant">
          {emptyText}
        </div>
      );
    }
    return (
      <div role="status" className="p-6 flex items-center justify-center gap-2 rounded-xl bg-surface-container border border-outline-variant/60 text-xs text-on-surface-variant">
        <Loader2 className="w-4 h-4 animate-spin text-ready-emerald" />
        <span>Loading from the server...</span>
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 text-left pb-16">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 bg-surface-container border border-outline-variant/60 rounded-2xl flex items-center justify-center shadow-xs text-on-surface">
            <SettingsIcon className="w-6 h-6 text-ready-emerald" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-on-surface">Settings & Preferences</h1>
              {isDemo && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  Sandbox Demo
                </span>
              )}
            </div>
            <p className="text-on-surface-variant text-xs mt-0.5">
              Manage organization identity, compliance scope baselines, API keys, webhooks, and visual preferences.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/connectors"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 transition-colors"
          >
            <Plug className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Connectors Fleet</span>
          </Link>
          <button
            onClick={checkApiHealth}
            className="p-2 text-on-surface-variant hover:text-on-surface bg-surface-container hover:bg-surface-container-high rounded-xl border border-outline-variant/60 transition-colors cursor-pointer"
            title="Refresh Diagnostics"
          >
            <RefreshCw className={`w-4 h-4 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Modern Navigation Tabs (6 Clean, Uncluttered Tabs) */}
      <div className="flex items-center gap-1.5 p-1 bg-surface-container rounded-2xl border border-outline-variant/60 overflow-x-auto shadow-xs scrollbar-none">
        {[
          { id: 'workspace' as const, label: 'Workspace & Team', icon: Building },
          { id: 'frameworks' as const, label: 'Regulatory Scope', icon: BookOpen, badge: frameworks.length > 0 ? frameworks.length : undefined },
          { id: 'apikeys' as const, label: 'API Keys & Ingest', icon: Key, badge: apiKeysBadge },
          { id: 'webhooks' as const, label: 'Webhooks & Auditor Links', icon: Share2, badge: webhooksBadge },
          { id: 'preferences' as const, label: 'Preferences', icon: SlidersHorizontal },
          { id: 'api' as const, label: 'API Explorer', icon: Code2 },
          { id: 'diagnostics' as const, label: 'System & Diagnostics', icon: Server },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-surface-container-low text-on-surface shadow-xs border border-outline-variant/40'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: WORKSPACE & TEAM                                                   */}
      {/* ========================================================================= */}
      {activeTab === 'workspace' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Active Organization Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald font-bold text-xs">
                    {orgName ? orgName.charAt(0).toUpperCase() : 'R'}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-on-surface">Organization Profile</h3>
                    <p className="text-[11px] text-on-surface-variant">Active tenant workspace</p>
                  </div>
                </div>
                <span className={`text-[10px] font-bold font-mono uppercase px-2 py-0.5 rounded-md border ${
                  isDemo
                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                }`}>
                  {isDemo ? 'Sandbox Demo' : 'Live Production'}
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-on-surface-variant block mb-1">Organization Name</span>
                  <div className="font-semibold text-on-surface text-sm">{orgName || 'Workspace'}</div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant text-[11px] block mb-0.5">Workspace Tier</span>
                    <span className="font-bold text-on-surface font-mono uppercase text-xs">
                      {tier || (isDemo ? 'Design Partner' : 'Enterprise')}
                    </span>
                  </div>
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant text-[11px] block mb-0.5">Environment</span>
                    <span className="font-bold text-on-surface font-mono text-xs">
                      {isDemo ? 'Synthetic Demo' : 'Verified Evidence'}
                    </span>
                  </div>
                </div>

                {/* Organization ID with Copy Action */}
                <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-on-surface-variant font-mono uppercase block mb-0.5">Tenant ID</span>
                    <code className="text-xs font-mono font-bold text-on-surface">{effectiveOrgId || 'demo-health-org'}</code>
                  </div>
                  <button
                    onClick={() => copyToClipboard(effectiveOrgId || 'demo-health-org', 'tenant-id', 'Tenant ID')}
                    className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg bg-surface-container-high border border-outline-variant/60 cursor-pointer"
                    title="Copy Tenant ID"
                  >
                    {copiedId === 'tenant-id' ? <Check className="w-3.5 h-3.5 text-ready-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                {orgs.length > 1 && (
                  <div className="pt-2">
                    <span className="text-on-surface-variant block mb-1.5 font-medium">Switch Organization</span>
                    <select
                      value={effectiveOrgId || ''}
                      onChange={(e) => selectOrg(e.target.value)}
                      className="w-full px-3 py-2 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-xs focus:outline-none focus:border-ready-emerald"
                    >
                      {orgs.map((org) => (
                        <option key={org.id} value={org.id} className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">
                          {org.name} ({org.id.slice(0, 10)}...)
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* User Account & Session Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5 pb-3 border-b border-outline-variant/60">
                <User className="w-5 h-5 text-on-surface-variant" />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">Authenticated Member</h3>
                  <p className="text-[11px] text-on-surface-variant">Current user credentials</p>
                </div>
              </div>

              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 bg-ready-emerald/15 border border-ready-emerald/30 rounded-full flex items-center justify-center text-ready-emerald font-bold text-base shadow-sm shrink-0">
                  {user?.photoURL ? (
                    <img src={user.photoURL} alt="User" className="w-12 h-12 rounded-full object-cover" />
                  ) : (
                    <span>{user?.displayName?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}</span>
                  )}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-on-surface text-sm truncate">{user?.displayName || 'Authorized User'}</div>
                  <div className="text-xs text-on-surface-variant flex items-center gap-1.5 mt-0.5 truncate">
                    <Mail className="w-3.5 h-3.5 shrink-0" />
                    <span>{user?.email || 'user@organization.resilai.io'}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-outline-variant/60 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5 text-ready-emerald" />
                    Member ID
                  </span>
                  <code className="bg-surface-container border border-outline-variant/60 px-2 py-0.5 rounded font-mono text-[11px] text-on-surface">
                    {user?.uid ? `${user.uid.slice(0, 14)}...` : 'demo-auth-session'}
                  </code>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant flex items-center gap-1">
                    <Key className="w-3.5 h-3.5 text-ready-emerald" />
                    Auth Provider
                  </span>
                  <span className="font-mono font-semibold text-on-surface text-[11px]">
                    {user?.providerId || (isDemo ? 'Sandbox Session' : 'Firebase Auth')}
                  </span>
                </div>

                <div className="pt-3 border-t border-outline-variant/60 flex items-center justify-between">
                  <button
                    onClick={async () => {
                      await signOut();
                      window.location.href = '/login';
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-xs font-semibold text-rose-600 dark:text-rose-400 border border-outline-variant/60 transition-colors cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{isDemo ? 'Exit Demo Sandbox' : 'Sign Out of Account'}</span>
                  </button>
                  <span className="text-[10px] text-on-surface-variant/70 font-mono">Session Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* Visual Appearance & Theme Controls */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-on-surface">Visual Appearance & Interface Mode</h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Toggle between Material 3 Obsidian dark mode and high-contrast clinical light mode.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              {[
                { id: 'light' as const, label: 'Light Theme', desc: 'Clinical High Contrast', icon: Sun },
                { id: 'dark' as const, label: 'Dark Theme', desc: 'Stitch Obsidian Slate', icon: Moon },
                { id: 'system' as const, label: 'System Default', desc: 'Sync with Device OS', icon: Laptop },
              ].map((themeOption) => {
                const Icon = themeOption.icon;
                const isSelected = themeContext?.theme === themeOption.id;
                return (
                  <button
                    key={themeOption.id}
                    onClick={() => themeContext?.setTheme(themeOption.id)}
                    className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center gap-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-surface-container border-ready-emerald text-on-surface shadow-xs ring-1 ring-ready-emerald/50'
                        : 'bg-surface-container/60 hover:bg-surface-container border-outline-variant/60 text-on-surface-variant'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
                    <div>
                      <div className={`text-xs font-bold ${isSelected ? 'text-on-surface' : 'text-on-surface-variant'}`}>
                        {themeOption.label}
                      </div>
                      <div className="text-[10px] text-on-surface-variant/70 mt-0.5">{themeOption.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subscription & Customer Portal Card */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pb-3 border-b border-outline-variant/60">
              <div className="flex items-center gap-2.5">
                <CreditCard className="w-5 h-5 text-ready-emerald" />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">Subscription & Entitlements</h3>
                  <p className="text-[11px] text-on-surface-variant">Stripe enterprise subscription tier</p>
                </div>
              </div>
              <button
                onClick={handleOpenBillingPortal}
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-xl border border-outline-variant/60 text-xs font-semibold transition-colors cursor-pointer"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open Stripe Customer Portal</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[11px] block mb-1">Current Plan</span>
                <span className="text-sm font-bold text-on-surface font-mono uppercase">{tier || 'Design Partner'}</span>
              </div>
              <div className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[11px] block mb-1">Evidence Retention</span>
                <span className="text-sm font-bold text-ready-emerald font-mono">365 Days WORM</span>
              </div>
              <div className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[11px] block mb-1">Active Connectors</span>
                <span className="text-sm font-bold text-on-surface font-mono">Unlimited Ingest</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: REGULATORY SCOPE                                                    */}
      {/* ========================================================================= */}
      {activeTab === 'frameworks' && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-4 border-b border-outline-variant/60">
              <div>
                <h3 className="text-base font-bold text-on-surface">Regulatory & Framework Scope Profiles</h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Toggling operational scope dynamically recalculates applicable compliance requirements in real-time.
                </p>
              </div>
              {loadingProfile && (
                <div className="flex items-center gap-2 text-xs font-mono text-ready-emerald">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Recalculating...</span>
                </div>
              )}
            </div>

            {/* Profile Toggles Grid */}
            <div className="grid md:grid-cols-2 gap-4">
              {profileConfigs.map((config) => {
                const Icon = config.icon;
                const isEnabled = profile ? !!profile[config.key] : false;
                const isUpdating = updatingProfile === config.key;

                return (
                  <div
                    key={config.key}
                    className={`p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between gap-3 ${
                      isEnabled
                        ? 'bg-surface-container border-ready-emerald/40 shadow-xs'
                        : 'bg-surface-container/40 border-outline-variant/40 hover:border-outline-variant/70'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${config.color}`}>
                        <Icon className="w-4.5 h-4.5" />
                      </div>
                      <div className="space-y-0.5 flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-on-surface truncate">{config.title}</h4>
                          <span className="text-[10px] text-on-surface-variant/70 font-mono uppercase">{config.category}</span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant leading-relaxed line-clamp-2">
                          {config.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-outline-variant/40 text-xs">
                      <span className={`text-[10px] uppercase font-bold tracking-wider font-mono ${
                        isEnabled ? 'text-ready-emerald' : 'text-on-surface-variant/60'
                      }`}>
                        {isEnabled ? 'Active Baseline' : 'Advisory / Inactive'}
                      </span>
                      <button
                        role="switch"
                        aria-checked={isEnabled}
                        disabled={isUpdating || !profile}
                        onClick={() => handleProfileToggle(config.key, !isEnabled)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none cursor-pointer disabled:opacity-50 ${
                          isEnabled ? 'bg-ready-emerald' : 'bg-surface-container-highest border border-outline-variant'
                        }`}
                      >
                        {isUpdating ? (
                          <Loader2 className="w-3 h-3 text-slate-950 animate-spin mx-auto" />
                        ) : (
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                              isEnabled ? 'translate-x-4.5' : 'translate-x-0.5'
                            }`}
                          />
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Regions: the laws listed below depend on where the organisation operates */}
            <div className="pt-6 border-t border-outline-variant/60 space-y-3" data-testid="region-picker">
              <h4 className="text-xs font-mono font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-ready-emerald" />
                <span>Where you operate</span>
              </h4>
              <p className="text-[11px] text-on-surface-variant leading-relaxed">
                Pick every region where you have clients, staff or data. The list below adds the laws
                for each one, such as the EU AI Act and GDPR in the EU, or the data protection law of each Gulf state.
              </p>
              <div className="flex flex-wrap gap-2">
                {OPERATING_REGIONS.map((region) => {
                  const selected = (profile?.geo_regions || []).includes(region.code);
                  return (
                    <button
                      key={region.code}
                      type="button"
                      aria-pressed={selected}
                      disabled={!profile || updatingProfile !== null}
                      onClick={() => handleRegionToggle(region.code)}
                      className={`px-3 py-1.5 rounded-full border text-[11px] font-semibold transition-colors disabled:opacity-60 ${
                        selected
                          ? 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/40'
                          : 'bg-surface-container text-on-surface-variant border-outline-variant/60 hover:border-ready-emerald/40'
                      }`}
                    >
                      {region.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Recalculated Frameworks List */}
            <div className="pt-6 border-t border-outline-variant/60 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-mono font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-ready-emerald" />
                  <span>Recalculated Compliance Obligations ({frameworks.length})</span>
                </h4>
                <Link to="/governance" className="text-xs text-ready-emerald hover:underline font-semibold flex items-center gap-1">
                  <span>View Governance Matrix</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {frameworks.length === 0 ? (
                <div className="p-6 text-center rounded-xl bg-surface-container border border-dashed border-outline-variant text-xs text-on-surface-variant">
                  Toggle on compliance profiles above to activate regulatory rules engines and mapping tables.
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {frameworks.map((fw) => (
                    <div
                      key={fw.framework}
                      className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/60 flex flex-col justify-between gap-2"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-bold font-mono text-on-surface">{fw.framework}</span>
                          <span
                            className={`px-1.5 py-0.2 text-[9px] font-bold rounded uppercase tracking-wider ${
                              fw.mandatory
                                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                                : 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20'
                            }`}
                          >
                            {fw.mandatory ? 'Mandatory' : 'Advisory'}
                          </span>
                        </div>
                        {fw.jurisdiction && (
                          <p className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant/80 mb-1">
                            {fw.jurisdiction}
                          </p>
                        )}
                        <p className="text-[11px] text-on-surface-variant leading-relaxed" title={fw.reason}>
                          {fw.reason}
                        </p>
                        {fw.evidence_note && (
                          <p className="text-[10px] text-on-surface-variant/80 leading-relaxed mt-1.5" data-testid="framework-evidence-note">
                            {fw.evidence_note}
                          </p>
                        )}
                      </div>

                      {fw.reference_url && (
                        <a
                          href={fw.reference_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] text-ready-emerald hover:underline font-semibold mt-1"
                        >
                          <span>Official Reference</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: API KEYS & INGEST TOKENS                                           */}
      {/* ========================================================================= */}
      {activeTab === 'apikeys' && (
        <div className="space-y-6 animate-fade-in">
          {isDemo && demoNotice}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pb-4 border-b border-outline-variant/60">
              <div>
                <h3 className="text-base font-bold text-on-surface">API Keys & Ingest Tokens</h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Secure programmatic access for log forwarders, OpenTelemetry agents, and automated audit reporting.
                </p>
              </div>
              <button
                onClick={() => {
                  setGeneratedSecret(null);
                  setModalError(null);
                  setShowKeyModal(true);
                }}
                disabled={!isDemo && !liveOrgId}
                className="inline-flex items-center gap-2 px-4 py-2 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-xs font-bold rounded-xl shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-4 h-4" />
                <span>Generate New API Key</span>
              </button>
            </div>

            {/* List of Configured Keys */}
            <div className="space-y-3">
              {renderSectionError(
                apiKeysLoad.status === 'error' ? apiKeysLoad.error : undefined,
                liveOrgId ? () => void loadApiKeys(liveOrgId) : undefined
              )}
              {renderSectionError(actionError.apikeys)}
              {renderListState(apiKeysLoad, apiKeys.length, 'No API keys yet.')}
              {apiKeys.map((k) => (
                <div
                  key={k.id}
                  className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 flex flex-col sm:flex-row justify-between sm:items-center gap-4 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-on-surface">{k.name || 'API key'}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20">
                        {k.scope}
                      </span>
                      {isDemo && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          Sample
                        </span>
                      )}
                      {!k.isActive && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                          Revoked
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant">
                      <code className="font-mono bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant/40">
                        {k.prefix}
                      </code>
                      <span>•</span>
                      <span>Created: {formatDate(k.createdAt)}</span>
                      <span>•</span>
                      {isDemo ? (
                        <span>Last used: {k.lastUsed || 'Never'}</span>
                      ) : (
                        <span>{k.lastUsedAt ? `Last used: ${formatDate(k.lastUsedAt)}` : 'Not used yet'}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => copyToClipboard(k.prefix, k.id, 'API Key Prefix')}
                      className="p-2 text-on-surface-variant hover:text-on-surface bg-surface-container-high rounded-xl border border-outline-variant/60 transition-colors cursor-pointer"
                      title="Copy Key Prefix"
                    >
                      {copiedId === k.id ? <Check className="w-4 h-4 text-ready-emerald" /> : <Copy className="w-4 h-4" />}
                    </button>
                    {k.isActive && (
                      <button
                        onClick={() => handleRevokeApiKey(k.id)}
                        disabled={busyId === k.id}
                        className="px-3 py-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                      >
                        {busyId === k.id ? 'Revoking...' : 'Revoke Key'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Developer Integration Code Snippet */}
            <div className="pt-4 border-t border-outline-variant/60 space-y-3">
              <h4 className="text-xs font-mono font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
                <Terminal className="w-4 h-4 text-ready-emerald" />
                <span>Example: Read the Latest Readiness Score via cURL</span>
              </h4>
              <div className="p-4 bg-surface-container-highest dark:bg-black/40 rounded-xl border border-outline-variant/60 text-xs font-mono overflow-x-auto relative">
                <button
                  onClick={() =>
                    copyToClipboard(
                      `curl "${apiBaseUrl}/api/external/latest-score" \\\n  -H "X-AIRS-API-Key: <YOUR_RESILAI_KEY>"`,
                      'curl-snippet',
                      'cURL Snippet'
                    )
                  }
                  className="absolute top-3 right-3 p-1.5 rounded-lg bg-surface-container border border-outline-variant/60 hover:text-on-surface text-on-surface-variant cursor-pointer"
                  title="Copy snippet"
                >
                  {copiedId === 'curl-snippet' ? <Check className="w-3.5 h-3.5 text-ready-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <pre className="text-on-surface leading-relaxed">
{`curl "${apiBaseUrl}/api/external/latest-score" \\
  -H "X-AIRS-API-Key: <YOUR_RESILAI_KEY>"`}
                </pre>
              </div>
              <p className="text-[11px] text-on-surface-variant">Needs a key with the scores:read scope.</p>
            </div>
          </div>

          {/* Modal for Creating New Key */}
          {showKeyModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 dark:bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-base font-bold text-on-surface">Generate Ingestion API Key</h3>
                  <button onClick={closeKeyModal} aria-label="Close" className="text-on-surface-variant hover:text-on-surface text-sm p-1 cursor-pointer">
                    ✕
                  </button>
                </div>

                {!generatedSecret ? (
                  <form onSubmit={handleCreateApiKey} className="space-y-4">
                    {isDemo && demoNotice}
                    {/* The server stores no label for a key, so a live workspace is not asked for one. */}
                    {isDemo && (
                      <div>
                        <label htmlFor="settings-key-name" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                          Key Name / Service Label
                        </label>
                        <input
                          id="settings-key-name"
                          type="text"
                          required
                          placeholder="e.g., Azure Backup Daemon or Wazuh Forwarder"
                          value={newKeyName}
                          onChange={(e) => setNewKeyName(e.target.value)}
                          className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                        />
                      </div>
                    )}

                    <div>
                      <label htmlFor="settings-key-scope" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                        Authorization Scope
                      </label>
                      <select
                        id="settings-key-scope"
                        value={newKeyScope}
                        onChange={(e) => setNewKeyScope(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                      >
                        {isDemo ? (
                          <>
                            <option value="telemetry:write" className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">telemetry:write (Ingest logs and health heartbeats)</option>
                            <option value="scores:read" className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">scores:read (Read daily readiness scores & reports)</option>
                            <option value="admin" className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">admin (Full tenant access)</option>
                          </>
                        ) : (
                          LIVE_API_KEY_SCOPES.map((scope) => (
                            <option key={scope.value} value={scope.value} className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">
                              {scope.label}
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    {renderSectionError(modalError ?? undefined)}

                    <div className="flex justify-end gap-2.5 pt-2">
                      <button
                        type="button"
                        onClick={() => setShowKeyModal(false)}
                        className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 bg-ready-emerald text-slate-950 text-xs font-bold rounded-xl hover:brightness-105 cursor-pointer disabled:opacity-50"
                      >
                        {saving ? 'Generating...' : 'Generate Key'}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-4">
                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      {isDemo
                        ? `${DEMO_NOTICE} This sample key does not work.`
                        : 'Copy your API secret now. For security purposes, it will not be displayed again.'}
                    </p>
                    <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60 flex items-center justify-between">
                      <code className="text-xs font-mono font-bold text-ready-emerald truncate pr-2">{generatedSecret}</code>
                      <button
                        onClick={() => copyToClipboard(generatedSecret, 'new-secret', 'API Secret')}
                        className="p-1.5 bg-surface-container-high rounded-lg text-on-surface border border-outline-variant/60 cursor-pointer"
                      >
                        {copiedId === 'new-secret' ? <Check className="w-3.5 h-3.5 text-ready-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <button
                      onClick={closeKeyModal}
                      className="w-full py-2 bg-ready-emerald text-slate-950 text-xs font-bold rounded-xl cursor-pointer"
                    >
                      Done / Close
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: WEBHOOKS & AUDITOR SHARE LINKS                                     */}
      {/* ========================================================================= */}
      {activeTab === 'webhooks' && (
        <div className="space-y-6 animate-fade-in">
          {isDemo && demoNotice}
          {/* Outbound SIEM Webhooks Card */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pb-4 border-b border-outline-variant/60">
              <div>
                <h3 className="text-base font-bold text-on-surface">Outbound SIEM & Incident Webhooks</h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Stream real-time alerts to Splunk, PagerDuty, Microsoft Sentinel, or Slack when readiness drifts.
                </p>
              </div>
              <button
                onClick={() => {
                  setModalError(null);
                  setShowWebhookModal(true);
                }}
                disabled={!isDemo && !liveOrgId}
                className="inline-flex items-center gap-2 px-4 py-2 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-xs font-bold rounded-xl shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-4 h-4" />
                <span>Add Webhook Endpoint</span>
              </button>
            </div>

            <div className="space-y-3">
              {renderSectionError(
                webhooksLoad.status === 'error' ? webhooksLoad.error : undefined,
                liveOrgId ? () => void loadWebhooks(liveOrgId) : undefined
              )}
              {renderSectionError(actionError.webhooks)}
              {renderListState(webhooksLoad, webhooks.length, 'No webhooks yet.')}
              {webhooks.map((wh) => (
                <div
                  key={wh.id}
                  className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 flex flex-col sm:flex-row justify-between sm:items-center gap-4"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-on-surface">{wh.description || 'Webhook endpoint'}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20">
                        {wh.status}
                      </span>
                      {isDemo && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          Sample
                        </span>
                      )}
                    </div>
                    <code className="text-xs font-mono text-on-surface-variant block truncate max-w-md">{wh.url}</code>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-on-surface-variant pt-1">
                      <span>Events: </span>
                      {wh.events.map((ev) => (
                        <span key={ev} className="px-1.5 py-0.2 rounded bg-surface-container-high border border-outline-variant/40 font-mono text-[10px]">
                          {ev}
                        </span>
                      ))}
                      {!isDemo && <span>• Created: {formatDate(wh.createdAt)}</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => handleTestWebhook(wh.id)}
                      disabled={busyId === `test-${wh.id}`}
                      className="px-3 py-1.5 text-xs font-semibold bg-surface-container-high hover:bg-surface-bright text-on-surface border border-outline-variant/60 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5 inline mr-1" />
                      {busyId === `test-${wh.id}` ? 'Sending...' : 'Test Ping'}
                    </button>
                    <button
                      onClick={() => handleDeleteWebhook(wh.id)}
                      disabled={busyId === wh.id}
                      className="px-3 py-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {busyId === wh.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Time-to-Live Auditor Share Links Card */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pb-4 border-b border-outline-variant/60">
              <div>
                <h3 className="text-base font-bold text-on-surface">Time-to-Live Auditor & Underwriter Links</h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Generate temporary, read-only verification tokens for external SOC 2 auditors or cyber insurers.
                </p>
              </div>
              <button
                onClick={() => {
                  setModalError(null);
                  setGeneratedAuditorUrl(null);
                  setShowAuditorModal(true);
                }}
                disabled={!isDemo && !liveOrgId}
                className="inline-flex items-center gap-2 px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 text-xs font-bold rounded-xl shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-4 h-4 text-ready-emerald" />
                <span>Create Auditor Access Link</span>
              </button>
            </div>

            <div className="space-y-3">
              {renderSectionError(
                auditorLoad.status === 'error' ? auditorLoad.error : undefined,
                liveOrgId ? () => void loadAuditorLinks(liveOrgId) : undefined
              )}
              {renderSectionError(actionError.auditor)}
              {renderListState(auditorLoad, auditorLinks.length, 'No auditor links yet.')}
              {auditorLinks.map((aud) => {
                // Sandbox samples carry a made-up token. A live row never shows one: the server does not list tokens.
                const shareUrl = isDemo ? `${window.location.origin}/auditor?token=${aud.token}` : null;
                return (
                  <div
                    key={aud.id}
                    className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 flex flex-col sm:flex-row justify-between sm:items-center gap-4"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-bold text-on-surface">{aud.auditorOrg || 'Auditor link'}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          Expires in {Math.max(1, Math.ceil((new Date(aud.expiresAt).getTime() - Date.now()) / 86400000))}d
                        </span>
                        {isDemo && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            Sample
                          </span>
                        )}
                      </div>
                      {isDemo ? (
                        <>
                          <p className="text-xs text-on-surface-variant">{aud.scope}</p>
                          <code className="text-[11px] font-mono bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant/40 block truncate max-w-sm mt-1">
                            {shareUrl}
                          </code>
                        </>
                      ) : (
                        <>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant">
                            <span>Created by: {aud.createdBy && aud.createdBy === user?.uid ? 'you' : aud.createdBy || 'unknown'}</span>
                            <span>•</span>
                            <span>Created: {formatDate(aud.createdAt)}</span>
                            <span>•</span>
                            <span>Expires: {formatDate(aud.expiresAt)}</span>
                            <span>•</span>
                            <span>Opened: {aud.accessCount ?? 0} time{aud.accessCount === 1 ? '' : 's'}</span>
                          </div>
                          {!aud.token && (
                            <p className="text-[11px] text-on-surface-variant/80 pt-1">
                              Created in an earlier session. The link is shown once and is not stored, so it cannot be revoked from here. It stops working on {formatDate(aud.expiresAt)}.
                            </p>
                          )}
                        </>
                      )}
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      {shareUrl && (
                        <button
                          onClick={() => copyToClipboard(shareUrl, aud.id, 'Sample auditor URL')}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-surface-container-high hover:bg-surface-bright text-on-surface border border-outline-variant/60 rounded-xl transition-colors cursor-pointer"
                        >
                          {copiedId === aud.id ? <Check className="w-3.5 h-3.5 text-ready-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>Copy URL</span>
                        </button>
                      )}
                      {(isDemo || aud.token) && (
                        <button
                          onClick={() => handleRevokeAuditorLink(aud)}
                          disabled={busyId === aud.id}
                          className="px-3 py-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                        >
                          {busyId === aud.id ? 'Revoking...' : 'Revoke'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Webhook Modal */}
          {showWebhookModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 dark:bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-base font-bold text-on-surface">Add Outbound Webhook</h3>
                  <button onClick={() => setShowWebhookModal(false)} aria-label="Close" className="text-on-surface-variant hover:text-on-surface text-sm p-1 cursor-pointer">
                    ✕
                  </button>
                </div>

                <form onSubmit={handleCreateWebhook} className="space-y-4">
                  {isDemo && demoNotice}
                  <div>
                    <label htmlFor="settings-webhook-url" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                      Destination URL
                    </label>
                    <input
                      id="settings-webhook-url"
                      type="url"
                      required
                      placeholder="https://siem.practice.com/webhook"
                      value={newWebhookUrl}
                      onChange={(e) => setNewWebhookUrl(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                    />
                  </div>

                  {isDemo ? (
                    <div>
                      <label htmlFor="settings-webhook-desc" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                        Description / Target
                      </label>
                      <input
                        id="settings-webhook-desc"
                        type="text"
                        placeholder="e.g., Splunk HEC or PagerDuty Sentinel"
                        value={newWebhookDesc}
                        onChange={(e) => setNewWebhookDesc(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                      />
                    </div>
                  ) : (
                    <div>
                      <label htmlFor="settings-webhook-secret" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                        Signing Secret (optional)
                      </label>
                      <input
                        id="settings-webhook-secret"
                        type="password"
                        autoComplete="off"
                        maxLength={255}
                        placeholder="Used to sign each delivery"
                        value={newWebhookSecret}
                        onChange={(e) => setNewWebhookSecret(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                      />
                      <p className="text-[11px] text-on-surface-variant mt-1.5">
                        Sends the <code className="font-mono">{LIVE_WEBHOOK_EVENTS.join(', ')}</code> event.
                      </p>
                    </div>
                  )}

                  {renderSectionError(modalError ?? undefined)}

                  <div className="flex justify-end gap-2.5 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowWebhookModal(false)}
                      className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={saving}
                      className="px-4 py-2 bg-ready-emerald text-slate-950 text-xs font-bold rounded-xl hover:brightness-105 cursor-pointer disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Webhook'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Auditor Link Modal */}
          {showAuditorModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 dark:bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-base font-bold text-on-surface">Generate Auditor Share Link</h3>
                  <button onClick={closeAuditorModal} aria-label="Close" className="text-on-surface-variant hover:text-on-surface text-sm p-1 cursor-pointer">
                    ✕
                  </button>
                </div>

                {generatedAuditorUrl ? (
                  <div className="space-y-4">
                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      Copy the link now. It is shown once and is not stored, so it cannot be displayed again.
                    </p>
                    <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60 flex items-center justify-between">
                      <code className="text-xs font-mono font-bold text-ready-emerald truncate pr-2">{generatedAuditorUrl}</code>
                      <button
                        onClick={() => copyToClipboard(generatedAuditorUrl, 'new-auditor-url', 'Auditor link')}
                        className="p-1.5 bg-surface-container-high rounded-lg text-on-surface border border-outline-variant/60 cursor-pointer"
                        title="Copy auditor link"
                      >
                        {copiedId === 'new-auditor-url' ? <Check className="w-3.5 h-3.5 text-ready-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <button
                      onClick={closeAuditorModal}
                      className="w-full py-2 bg-ready-emerald text-slate-950 text-xs font-bold rounded-xl cursor-pointer"
                    >
                      Done / Close
                    </button>
                  </div>
                ) : (
                <form onSubmit={handleCreateAuditorLink} className="space-y-4">
                  {isDemo && demoNotice}
                  {/* The server stores no auditor name, so a live workspace is not asked for one. */}
                  {isDemo && (
                    <div>
                      <label htmlFor="settings-auditor-name" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                        Auditor / Underwriter Entity Name
                      </label>
                      <input
                        id="settings-auditor-name"
                        type="text"
                        required
                        placeholder="e.g., A-LIGN SOC 2 Audit Team or Chubb Cyber Underwriting"
                        value={auditorOrgName}
                        onChange={(e) => setAuditorOrgName(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                      />
                    </div>
                  )}

                  <div>
                    <label htmlFor="settings-auditor-expiry" className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                      Expiration Duration
                    </label>
                    <select
                      id="settings-auditor-expiry"
                      value={auditorExpiryDays}
                      onChange={(e) => setAuditorExpiryDays(Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-sm focus:outline-none focus:border-ready-emerald"
                    >
                      <option value={7} className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">7 Days (Short assessment)</option>
                      <option value={14} className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">14 Days (Standard compliance audit)</option>
                      <option value={30} className="bg-surface text-on-surface dark:bg-surface-container dark:text-on-surface">30 Days (Annual underwriting renewal)</option>
                    </select>
                  </div>

                  {renderSectionError(modalError ?? undefined)}

                  <div className="flex justify-end gap-2.5 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowAuditorModal(false)}
                      className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={saving}
                      className="px-4 py-2 bg-ready-emerald text-slate-950 text-xs font-bold rounded-xl hover:brightness-105 cursor-pointer disabled:opacity-50"
                    >
                      {saving ? 'Generating...' : 'Generate Link'}
                    </button>
                  </div>
                </form>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: PREFERENCES (this browser only)                                    */}
      {/* ========================================================================= */}
      {activeTab === 'preferences' && (
        <div className="space-y-6 animate-fade-in">
          <p className="text-xs text-on-surface-variant">
            Saved in this browser only. They do not change your organisation's data or what your team sees.
          </p>

          {/* Start page */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div>
              <h3 id="pref-start-page-title" className="text-sm font-bold text-on-surface">Start page</h3>
              <p className="text-xs text-on-surface-variant mt-0.5">The page that opens after you sign in.</p>
            </div>

            <div role="radiogroup" aria-labelledby="pref-start-page-title" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
              {START_PAGE_OPTIONS.map((option) => {
                const isSelected = prefs.startPage === option.value;
                return (
                  <label
                    key={option.value}
                    className={`p-4 rounded-xl border flex items-start gap-3 transition-all cursor-pointer focus-within:ring-2 focus-within:ring-ready-emerald/60 ${
                      isSelected
                        ? 'bg-surface-container border-ready-emerald text-on-surface shadow-xs ring-1 ring-ready-emerald/50'
                        : 'bg-surface-container/60 hover:bg-surface-container border-outline-variant/60 text-on-surface-variant'
                    }`}
                  >
                    <input
                      type="radio"
                      name="pref-start-page"
                      value={option.value}
                      checked={isSelected}
                      onChange={() => setPrefs({ startPage: option.value })}
                      className="mt-0.5 h-4 w-4 shrink-0 accent-ready-emerald cursor-pointer"
                    />
                    <span className="min-w-0">
                      <span className={`block text-xs font-bold ${isSelected ? 'text-on-surface' : 'text-on-surface-variant'}`}>
                        {option.label}
                      </span>
                      <span className="block text-[10px] text-on-surface-variant/70 mt-0.5">{option.hint}</span>
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Network Map */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-on-surface">Network Map</h3>
              <p id="pref-map-view-title" className="text-xs text-on-surface-variant mt-0.5">Default view when the map opens.</p>
            </div>

            <div role="radiogroup" aria-labelledby="pref-map-view-title" className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              {MAP_VIEW_OPTIONS.map((option) => {
                const isSelected = prefs.mapView === option.value;
                return (
                  <label
                    key={option.value}
                    className={`p-4 rounded-xl border flex items-start gap-3 transition-all cursor-pointer focus-within:ring-2 focus-within:ring-ready-emerald/60 ${
                      isSelected
                        ? 'bg-surface-container border-ready-emerald text-on-surface shadow-xs ring-1 ring-ready-emerald/50'
                        : 'bg-surface-container/60 hover:bg-surface-container border-outline-variant/60 text-on-surface-variant'
                    }`}
                  >
                    <input
                      type="radio"
                      name="pref-map-view"
                      value={option.value}
                      checked={isSelected}
                      onChange={() => setPrefs({ mapView: option.value })}
                      className="mt-0.5 h-4 w-4 shrink-0 accent-ready-emerald cursor-pointer"
                    />
                    <span className="min-w-0">
                      <span className={`block text-xs font-bold ${isSelected ? 'text-on-surface' : 'text-on-surface-variant'}`}>
                        {option.label}
                      </span>
                      <span className="block text-[10px] text-on-surface-variant/70 mt-0.5">{option.hint}</span>
                    </span>
                  </label>
                );
              })}
            </div>

            <div className="flex items-start justify-between gap-4 p-4 bg-surface-container rounded-xl border border-outline-variant/60">
              <div className="min-w-0">
                <span id="pref-map-refresh-label" className="block text-xs font-bold text-on-surface">
                  Refresh from connected systems every 45 seconds
                </span>
                <span id="pref-map-refresh-hint" className="block text-[11px] text-on-surface-variant mt-0.5">
                  Only while the map is open. Turn off to load it once.
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={prefs.mapLiveRefresh}
                aria-labelledby="pref-map-refresh-label"
                aria-describedby="pref-map-refresh-hint"
                onClick={() => setPrefs({ mapLiveRefresh: !prefs.mapLiveRefresh })}
                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald/60 cursor-pointer ${
                  prefs.mapLiveRefresh ? 'bg-ready-emerald' : 'bg-surface-container-highest border border-outline-variant'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    prefs.mapLiveRefresh ? 'translate-x-4.5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Motion */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-on-surface">Motion</h3>
            </div>

            <div className="flex items-start justify-between gap-4 p-4 bg-surface-container rounded-xl border border-outline-variant/60">
              <div className="min-w-0">
                <span id="pref-reduce-motion-label" className="block text-xs font-bold text-on-surface">
                  Reduce motion
                </span>
                <span id="pref-reduce-motion-hint" className="block text-[11px] text-on-surface-variant mt-0.5">
                  Stops pulsing, sliding and auto-rotation.
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={prefs.reduceMotion}
                aria-labelledby="pref-reduce-motion-label"
                aria-describedby="pref-reduce-motion-hint"
                onClick={() => setPrefs({ reduceMotion: !prefs.reduceMotion })}
                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald/60 cursor-pointer ${
                  prefs.reduceMotion ? 'bg-ready-emerald' : 'bg-surface-container-highest border border-outline-variant'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    prefs.reduceMotion ? 'translate-x-4.5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <button
              type="button"
              onClick={() => {
                resetPreferences();
                addToast({
                  title: 'Preferences Reset',
                  message: 'Back to the defaults for this browser.',
                  type: 'info',
                });
              }}
              className="inline-flex items-center justify-center gap-2 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5 text-on-surface-variant" />
              <span>Reset preferences</span>
            </button>
            <p className="text-[10px] text-on-surface-variant/70">Puts every choice on this tab back to its default.</p>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 6: SYSTEM & DIAGNOSTICS                                               */}
      {/* ========================================================================= */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Live API Health Diagnostic Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                <div className="flex items-center gap-2.5">
                  <Server className="w-5 h-5 text-on-surface-variant" />
                  <div>
                    <h3 className="text-sm font-bold text-on-surface">API Connection Diagnostics</h3>
                    <p className="text-[11px] text-on-surface-variant">Cloud Run service health</p>
                  </div>
                </div>
                <button
                  onClick={checkApiHealth}
                  disabled={health.status === 'checking'}
                  className="p-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 text-xs transition-colors cursor-pointer"
                  title="Check latency"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex items-center gap-3 p-3.5 bg-surface-container rounded-xl border border-outline-variant/60">
                {health.status === 'checking' && (
                  <>
                    <div className="w-2.5 h-2.5 bg-amber-400 rounded-full animate-ping" />
                    <span className="text-xs font-bold text-amber-500">Pinging Service...</span>
                  </>
                )}
                {health.status === 'ok' && (
                  <>
                    <CheckCircle className="w-4 h-4 text-ready-emerald" />
                    <div className="flex-1 flex justify-between items-center">
                      <span className="text-xs font-bold text-ready-emerald">Operational</span>
                      {health.latencyMs !== undefined && (
                        <span className="text-[11px] font-mono text-on-surface-variant">{health.latencyMs} ms latency</span>
                      )}
                    </div>
                  </>
                )}
                {health.status === 'error' && (
                  <>
                    <XCircle className="w-4 h-4 text-rose-500" />
                    <span className="text-xs font-bold text-rose-500">Service Degraded</span>
                  </>
                )}
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-on-surface-variant block mb-1">API Base URL</span>
                  <code className="text-[11px] bg-surface-container border border-outline-variant/60 px-3 py-1.5 rounded-xl font-mono text-on-surface block truncate">
                    {apiBaseUrl}
                  </code>
                </div>

                {health.lastChecked && (
                  <p className="text-[10px] text-on-surface-variant/70">
                    Last validated: {health.lastChecked.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>

            {/* Local Cache & Session Storage Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                  <div className="flex items-center gap-2.5">
                    <Database className="w-5 h-5 text-on-surface-variant" />
                    <div>
                      <h3 className="text-sm font-bold text-on-surface">Local Client Cache</h3>
                      <p className="text-[11px] text-on-surface-variant">Cached browser states</p>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-on-surface-variant">
                    {localDataSummary.length} item{localDataSummary.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="pt-2">
                  {localDataSummary.length > 0 ? (
                    <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                      {localDataSummary.slice(0, 5).map((item) => (
                        <div key={item.key} className="flex justify-between items-center text-xs bg-surface-container px-3 py-1.5 rounded-lg border border-outline-variant/40">
                          <code className="font-mono text-on-surface text-[11px] truncate max-w-[200px]">{item.key}</code>
                          <span className="text-on-surface-variant text-[10px] font-mono">
                            {item.size < 1024 ? `${item.size} B` : `${(item.size / 1024).toFixed(1)} KB`}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-on-surface-variant/70 italic py-2">No local cache data recorded.</p>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-outline-variant/60 flex items-center justify-between gap-3">
                <button
                  onClick={handleClearLocalData}
                  disabled={clearingData}
                  className="inline-flex items-center gap-2 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Trash2 className={`w-3.5 h-3.5 ${clearingData ? 'animate-pulse text-rose-500' : 'text-on-surface-variant'}`} />
                  <span>{clearingData ? 'Flushing...' : 'Flush Cache'}</span>
                </button>
                <p className="text-[10px] text-on-surface-variant/70 text-right leading-tight max-w-[220px]">
                  Flushing cache resets temporary client states without affecting server verification data.
                </p>
              </div>
            </div>
          </div>

          {/* Release & Build Manifest Card (Single Consolidated Instance) */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-5 h-5 text-ready-emerald" />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">Release & Build Manifest</h3>
                  <p className="text-[11px] text-on-surface-variant">Continuous integration build telemetry</p>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/20 px-2 py-0.5 rounded-full uppercase">
                Verified Engine
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[10px] uppercase font-mono block mb-1">Git Commit</span>
                <span className="font-mono font-bold text-on-surface text-xs truncate block">
                  {((window as any).__RESILAI_BUILD__?.commit) || 'main (HEAD)'}
                </span>
              </div>
              <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[10px] uppercase font-mono block mb-1">Target Environment</span>
                <span className="font-mono font-bold text-on-surface text-xs capitalize">
                  {((window as any).__RESILAI_BUILD__?.environment) || (isDemo ? 'Sandbox Demo' : 'Cloud Run Live')}
                </span>
              </div>
              <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[10px] uppercase font-mono block mb-1">Scoring Mode</span>
                <span className="font-mono font-bold text-ready-emerald text-xs">
                  Deterministic
                </span>
              </div>
              <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                <span className="text-on-surface-variant text-[10px] uppercase font-mono block mb-1">Build Timestamp</span>
                <span className="font-mono text-on-surface text-xs truncate block">
                  {((window as any).__RESILAI_BUILD__?.buildTime) ? new Date((window as any).__RESILAI_BUILD__.buildTime).toLocaleDateString() : 'Live Cloud'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* API explorer: read the reference and test live endpoints without leaving the app. */}
      {activeTab === 'api' && (
        <div className="space-y-4 animate-fade-in" data-testid="settings-api-explorer">
          <ApiExplorerLazy title="API Explorer" />
        </div>
      )}
    </div>
  );
}
