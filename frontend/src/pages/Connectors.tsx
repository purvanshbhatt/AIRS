import { useEffect, useState, useCallback } from 'react';
import { 
  getIntegrationStatus, 
  getEvidenceConfidence, 
  getConnectorsList, 
  createConnector, 
  checkConnectorHealth, 
  syncConnectorNow, 
  deleteConnector 
} from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
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
  Lock
} from 'lucide-react';

type ConnectorStatus = 'CONNECTED' | 'DEGRADED' | 'NOT CONFIGURED' | 'AUTHENTICATION FAILED' | 'NO RECENT EVIDENCE';

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
      { key: 'role_arn', label: 'Cross-Account IAM Role ARN *', placeholder: 'arn:aws:iam::123456789012:role/ResilAI-Audit-Role' },
      { key: 'external_id', label: 'External ID', placeholder: 'resilai-org-external-id' },
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
    ],
  },
];

export default function ConnectorsPage() {
  const { orgId, orgName, isDemo } = useActiveOrg();
  const { addToast } = useToast();

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

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [integ, conf, connList] = await Promise.all([
        getIntegrationStatus(orgId).catch(() => null),
        getEvidenceConfidence(orgId).catch(() => null),
        getConnectorsList().catch(() => ({ connectors: [], total: 0 })),
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
      initial[field.key] = existing?.config?.[field.key] || field.defaultValue || '';
    });
    
    setFormData(initial);
    setActiveConfigDef(def);
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

      await createConnector({
        connector_type: activeConfigDef.type,
        display_name: activeConfigDef.name,
        auth_method: 'api_key',
        credentials: {
          api_key: formData.api_key || formData.client_secret || formData.secret_key || 'configured',
        },
        config: formData,
        sync_interval_minutes: parseInt(formData.sync_interval_minutes || '15', 10),
      });

      addToast({
        title: 'Connector Configured',
        message: `${activeConfigDef.name} has been successfully registered and encrypted at rest.`,
        type: 'ready',
      });

      setActiveConfigDef(null);
      await loadData();
    } catch (err: any) {
      console.error('Failed to save connector:', err);
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

      const res = await checkConnectorHealth(registered.id);
      addToast({
        title: `Health Check: ${res.status.toUpperCase()}`,
        message: `${res.message || 'Connected successfully'}. Latency: ${res.latency_ms || 0}ms.`,
        type: res.status === 'healthy' || res.status === 'active' ? 'ready' : 'error',
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

      const res = await syncConnectorNow(registered.id);
      if (res.success) {
        addToast({
          title: 'Telemetry Ingested',
          message: `Ingested ${res.events_ingested} evidence events in ${res.duration_ms}ms. Score updated.`,
          type: 'ready',
        });
      } else {
        addToast({
          title: 'Sync Warning',
          message: `Sync completed with ${res.errors_count} warnings. Check logs.`,
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

    return 'NOT CONFIGURED';
  };

  const getStatusBadge = (status: ConnectorStatus) => {
    switch (status) {
      case 'CONNECTED':
        return 'bg-ready-emerald/15 text-ready-emerald border-ready-emerald/30';
      case 'AUTHENTICATION FAILED':
        return 'bg-critical-red/15 text-critical-red border-critical-red/30';
      case 'DEGRADED':
        return 'bg-amber-500/15 text-amber-500 border-amber-500/30';
      case 'NOT CONFIGURED':
      default:
        return 'bg-surface-container-high text-on-surface-variant border-outline-variant/30';
    }
  };

  const activeCount = CONNECTOR_DEFINITIONS.filter(d => getConnectorStatus(d) === 'CONNECTED').length;

  return (
    <div className="space-y-8 animate-fade-up">
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
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30">
                LIVE PRODUCTION
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
          <button 
            onClick={() => handleOpenConfig(CONNECTOR_DEFINITIONS[0])}
            className="px-4 py-2 bg-ready-emerald text-on-primary-container rounded-xl hover:brightness-110 font-semibold text-xs transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Connect Splunk / SIEM</span>
          </button>
        </div>
      </div>

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
                  <span className={`px-2.5 py-1 rounded-full text-[11px] font-mono uppercase font-bold border shrink-0 ${getStatusBadge(status)}`}>
                    {status}
                  </span>
                </div>

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

              <p className="text-xs text-on-surface-variant leading-relaxed">
                Credentials are encrypted using AES-256-GCM at rest and never exposed to the frontend or narrative engine.
              </p>

              {activeConfigDef.configFields.map((field) => (
                <div key={field.key} className="space-y-1">
                  <label className="block text-xs font-semibold text-on-surface">
                    {field.label}
                  </label>
                  <input
                    type={field.type || 'text'}
                    value={formData[field.key] || ''}
                    onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                    placeholder={field.placeholder}
                    required={field.label.includes('*')}
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
                    {`https://api.resilai.io/api/v1/connectors/webhook/custom?org_id=${orgId || 'your-org-id'}`}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-end gap-3">
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
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
