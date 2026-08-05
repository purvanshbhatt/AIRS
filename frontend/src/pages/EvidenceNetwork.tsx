import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useIsReadOnly, useDemoMode } from '../contexts';
import {
  createApiKey,
  listApiKeys,
  revokeApiKey,
  createWebhook,
  listWebhooks,
  deleteWebhook,
  testWebhook,
  testWebhookUrl,
  seedMockSplunkFindings,
  getExternalFindings,
  getOrganizations,
  ApiRequestError,
  configureSplunkMcp,
  getSplunkConfig,
  removeSplunkConfig,
  pullSplunkEvidence,
  configureWazuh,
  getWazuhAgentStatus,
  getIntegrationStatus,
  getEvidenceConfidence,
  OrgConfidenceResponse,
} from '../api';
import type { Organization, ApiKeyMetadata, ApiKeyCreateResponse, ExternalFinding, Webhook } from '../types';
import type { SplunkEvidenceResponse } from '../api';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Select,
  Badge,
} from '../components/ui';
import {
  KeyRound,
  Webhook as WebhookIcon,
  Copy,
  CheckCircle2,
  ShieldCheck,
  PlugZap,
  Database,
  RefreshCw,
  TrendingUp,
  Activity,
  AlertTriangle,
  Server,
  Lock,
} from 'lucide-react';
import { ConnectorActivityPanel } from '../components/ConnectorActivityPanel';
import { ConfidenceGauge } from '../components/evidence/ConfidenceGauge';

export function EvidenceNetwork() {
  const isReadOnly = useIsReadOnly();
  const { isDemoMode } = useDemoMode();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  
  // Tab control
  const [activeTab, setActiveTab] = useState<'network' | 'wazuh' | 'splunk' | 'webhooks'>('network');

  // Integrations state
  const [apiKeys, setApiKeys] = useState<ApiKeyMetadata[]>([]);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [externalFindings, setExternalFindings] = useState<ExternalFinding[]>([]);
  const [splunkConnected, setSplunkConnected] = useState(false);
  const [newKey, setNewKey] = useState<ApiKeyCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [webhookTestUrl, setWebhookTestUrl] = useState('');
  const [webhookTestResult, setWebhookTestResult] = useState('');
  const [webhookTestPayload, setWebhookTestPayload] = useState('');

  // Splunk MCP configuration
  const [splunkBaseUrl, setSplunkBaseUrl] = useState('');
  const [splunkHecToken, setSplunkHecToken] = useState('');
  const [splunkConfigured, setSplunkConfigured] = useState(false);
  const [splunkConfigUrl, setSplunkConfigUrl] = useState('');

  // Wazuh connection state
  const [wazuhHost, setWazuhHost] = useState('');
  const [wazuhPort, setWazuhPort] = useState(55000);
  const [wazuhApiKey, setWazuhApiKey] = useState('');
  const [wazuhConfigured, setWazuhConfigured] = useState(false);
  const [wazuhConnected, setWazuhConnected] = useState(false);
  const [wazuhSyncing, setWazuhSyncing] = useState(false);

  const [evidenceResults, setEvidenceResults] = useState<SplunkEvidenceResponse | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);

  // Confidence score state
  const [confidenceData, setConfidenceData] = useState<OrgConfidenceResponse | null>(null);
  const [confidenceLoading, setConfidenceLoading] = useState(false);
  const [confidenceError, setConfidenceError] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const selectedOrgName = useMemo(
    () => organizations.find((o) => o.id === selectedOrgId)?.name || 'Organization',
    [organizations, selectedOrgId]
  );

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError('');
      try {
        const orgs = await getOrganizations();
        setOrganizations(orgs);
        if (orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load organizations');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const reload = async () => {
    if (!selectedOrgId) return;
    setError('');
    setNotice('');
    try {
      const [keys, hooks, findings, integrationStatus] = await Promise.all([
        listApiKeys(selectedOrgId),
        listWebhooks(selectedOrgId),
        getExternalFindings({ source: 'splunk', limit: 50, orgId: selectedOrgId }),
        getIntegrationStatus(selectedOrgId),
      ]);
      setApiKeys(keys);
      setWebhooks(hooks);
      setExternalFindings(findings);
      setSplunkConnected(findings.length > 0);
      const isWazuhConfigured = integrationStatus.wazuh_status === 'configured';
      setWazuhConfigured(isWazuhConfigured);
      if (isWazuhConfigured) {
        setWazuhHost(integrationStatus.wazuh_host || '');
        setWazuhPort(integrationStatus.wazuh_port || 55000);
      } else {
        setWazuhHost('');
        setWazuhPort(55000);
      }
      
      // Check if Splunk MCP is configured
      try {
        const cfg = await getSplunkConfig(selectedOrgId);
        setSplunkConfigured(cfg.configured);
        setSplunkConfigUrl(cfg.base_url || '');
      } catch {
        setSplunkConfigured(false);
      }

      // Fetch evidence confidence score
      fetchConfidence();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to synchronize integration profiles');
    }
  };

  const fetchConfidence = async () => {
    setConfidenceLoading(true);
    setConfidenceError(null);
    try {
      const data = await getEvidenceConfidence(selectedOrgId);
      setConfidenceData(data);
    } catch (err) {
      setConfidenceError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to calculate evidence confidence.');
    } finally {
      setConfidenceLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedOrgId) return;
    reload();
  }, [selectedOrgId]);

  const handleCopy = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleCreateApiKey = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    setNewKey(null);
    try {
      const result = await createApiKey(selectedOrgId);
      setNewKey(result);
      await reload();
      setNotice('New API key generated successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate key');
    } finally {
      setBusy(false);
    }
  };

  const handleRevokeApiKey = async (id: string) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await revokeApiKey(id);
      await reload();
      setNotice('API key revoked.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke key');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateWebhook = async () => {
    if (!selectedOrgId || !webhookUrl.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await createWebhook(selectedOrgId, {
        url: webhookUrl.trim(),
        secret: webhookSecret.trim() || undefined,
      });
      setWebhookUrl('');
      setWebhookSecret('');
      await reload();
      setNotice('Webhook registered.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register webhook');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await deleteWebhook(id);
      await reload();
      setNotice('Webhook disabled.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete webhook');
    } finally {
      setBusy(false);
    }
  };

  const handleTestWebhook = async (id: string) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const res = await testWebhook(id);
      if (res.delivered) {
        setNotice(`Test webhook delivered successfully (HTTP ${res.status_code || 200}).`);
      } else {
        setError(`Delivery failed: ${res.error || 'Unknown HTTP response'}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger test webhook');
    } finally {
      setBusy(false);
    }
  };

  const handleConnectSplunk = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await seedMockSplunkFindings(selectedOrgId);
      setSplunkConnected(result.connected);
      await reload();
      setNotice(`Splunk connected. ${result.inserted} synthetic findings ingested.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Splunk');
    } finally {
      setBusy(false);
    }
  };

  const handleSeedFindings = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await seedMockSplunkFindings(selectedOrgId);
      await reload();
      setNotice(`${result.inserted} additional synthetic Splunk findings ingested.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed findings');
    } finally {
      setBusy(false);
    }
  };

  const handleconfigureSplunkMcp = async () => {
    if (!selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await configureSplunkMcp(selectedOrgId, splunkBaseUrl.trim(), splunkHecToken.trim());
      setSplunkConfigured(true);
      setSplunkConfigUrl(splunkBaseUrl.trim());
      setSplunkHecToken('');
      setNotice('Splunk MCP configured successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to configure Splunk MCP');
    } finally {
      setBusy(false);
    }
  };

  const handleRemoveSplunkConfig = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await removeSplunkConfig(selectedOrgId);
      setSplunkConfigured(false);
      setSplunkConfigUrl('');
      setEvidenceResults(null);
      setNotice('Splunk MCP configuration removed.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove Splunk config');
    } finally {
      setBusy(false);
    }
  };

  const handlePullEvidence = async () => {
    if (!selectedOrgId) return;
    setEvidenceLoading(true);
    setError('');
    setNotice('');
    try {
      const result = await pullSplunkEvidence(selectedOrgId);
      setEvidenceResults(result);
      if (result.overall_status === 'verified') {
        setNotice(`All ${result.verified_controls} controls verified via Splunk evidence.`);
      } else if (result.overall_status === 'partial') {
        setNotice(`${result.verified_controls}/${result.total_controls} controls verified via Splunk.`);
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pull Splunk evidence');
    } finally {
      setEvidenceLoading(false);
    }
  };

  const handleTestWebhookUrl = async () => {
    if (!webhookTestUrl.trim()) return;
    setBusy(true);
    setError('');
    setWebhookTestResult('');
    setWebhookTestPayload('');
    try {
      const result = await testWebhookUrl(webhookTestUrl.trim());
      if (result.delivered) {
        setWebhookTestResult(`Delivered (HTTP ${result.status_code || 200}).`);
      } else {
        setWebhookTestResult(result.error || `Failed (HTTP ${result.status_code || 'unknown'}).`);
      }
      setWebhookTestPayload(JSON.stringify(result.payload, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Webhook delivery check failed');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
        <p className="text-sm text-slate-500 dark:text-slate-400 font-bold">Synchronizing Evidence Network...</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="max-w-6xl mx-auto space-y-6 text-left"
    >
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-blue-50/15 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 flex items-center justify-center">
            <ShieldCheck className="h-5 w-5 text-blue-650 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Evidence Network & Health Check</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              Is our security data fresh and mathematically verified?
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            aria-label="Select Organization"
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
          <Button size="sm" variant="outline" onClick={reload} disabled={busy} className="gap-2 rounded-xl font-bold">
            <RefreshCw className={`w-3.5 h-3.5 ${busy ? 'animate-spin' : ''}`} />
            Sync Network
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 bg-red-50/20 dark:bg-red-950/10 border border-red-200 dark:border-red-900/40 rounded-2xl text-xs text-red-700 dark:text-red-400 font-bold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
          {error}
        </div>
      )}
      {notice && (
        <div className="p-3.5 bg-green-50/20 dark:bg-green-950/10 border border-green-200 dark:border-green-900/40 rounded-2xl text-xs text-green-750 dark:text-green-400 font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#00C853] shrink-0" />
          {notice}
        </div>
      )}

      {/* Tabs Selector */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-bold text-slate-500 dark:text-slate-400">
        {(['network', 'wazuh', 'splunk', 'webhooks'] as const).map((tab) => (
          <button
            key={tab}
            className={`pb-3 capitalize border-b-2 transition-all relative ${
              activeTab === tab 
                ? 'text-indigo-600 border-indigo-650 dark:text-indigo-400 dark:border-indigo-400' 
                : 'border-transparent hover:text-slate-900 dark:hover:text-slate-200'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'network' ? 'Health Check Summary' : tab === 'wazuh' ? 'Wazuh Telemetry' : tab === 'splunk' ? 'Splunk MCP Ingestion' : 'API Webhooks Gateway'}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {/* Verification Summary Tab */}
        {activeTab === 'network' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Confidence Gauge Widget */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md p-6 flex flex-col items-center justify-center text-center">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Evidence Confidence Score</h3>
                <ConfidenceGauge score={confidenceData?.aggregate_score ?? null} size="lg" isLoading={confidenceLoading} />
                <div className="mt-4 text-xs font-semibold text-slate-500 dark:text-slate-450">
                  Aggregate score of active telemetry connectors and validation freshness.
                </div>
              </Card>

              {/* Factors Card */}
              <Card className="lg:col-span-2 rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md p-6">
                <h3 className="text-xs font-bold text-slate-405 uppercase tracking-wider mb-4 text-left">Confidence Composition Factors</h3>
                <div className="space-y-4">
                  {confidenceData?.connectors.map((conn) => (
                    <div key={conn.connector_name} className="border-b border-slate-200/50 dark:border-slate-800/40 last:border-0 pb-3 last:pb-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-slate-900 dark:text-slate-100 capitalize">{conn.connector_name} Agent</span>
                        <Badge variant={conn.confidence_score >= 80 ? 'success' : 'warning'} className="font-bold text-[10px]">
                          {conn.confidence_score}% Confidence
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2 font-mono text-[10px]">
                        {Object.entries(conn.factors).map(([factor, val]) => (
                          <div key={factor} className="p-2 rounded bg-slate-50 dark:bg-slate-900/65 border border-slate-200/40 dark:border-slate-800/40">
                            <span className="text-slate-400 block capitalize">{factor.replace(/_/g, ' ')}</span>
                            <span className="text-slate-800 dark:text-slate-200 font-bold block mt-0.5">{(val * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  {!confidenceData?.connectors.length && (
                    <p className="text-xs text-slate-500 italic text-left">No active connectors registered to analyze factors.</p>
                  )}
                </div>
              </Card>
            </div>

            {/* Active Integrations Grid */}
            <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md">
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <PlugZap className="w-5 h-5 text-indigo-500" />
                  Active Integrations
                </CardTitle>
                <CardDescription className="text-xs font-semibold">Live verification status for enterprise integration nodes.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 border border-slate-200/60 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Wazuh Manager</span>
                    <div className="text-xs font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                      {wazuhConnected ? 'Active Connection' : wazuhConfigured ? 'Connection Offline' : 'Not Connected'}
                    </div>
                  </div>
                  <div className="p-4 border border-slate-200/60 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Splunk MCP Ingestion</span>
                    <div className="text-xs font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                      {splunkConnected ? 'HEC Feed Active' : splunkConfigured ? 'HEC Inactive' : 'Not Connected'}
                    </div>
                  </div>
                  <div className="p-4 border border-slate-200/60 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">API Webhooks</span>
                    <div className="text-xs font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                      {webhooks.length > 0 ? `${webhooks.length} Active Gateway(s)` : 'Inactive'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Wazuh Telemetry Tab */}
        {activeTab === 'wazuh' && (
          <div className="space-y-6">
            {wazuhSyncing ? (
              <ConnectorActivityPanel
                orgId={selectedOrgId}
                host={wazuhHost}
                port={Number(wazuhPort)}
                onClose={() => setWazuhSyncing(false)}
                onSuccess={() => {
                  setWazuhSyncing(false);
                  setWazuhConfigured(true);
                  setWazuhConnected(true);
                }}
              />
            ) : (
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-slate-105 font-extrabold text-base flex items-center gap-2">
                    <PlugZap className="h-5 w-5 text-indigo-500" />
                    Wazuh Manager Integration
                  </CardTitle>
                  <CardDescription className="text-xs font-semibold">
                    Connect a Wazuh manager to pull agent status and vulnerability telemetry.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 border border-slate-200/60 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">Wazuh Manager Hook</h3>
                      <Badge variant={wazuhConnected ? 'success' : 'outline'} className="gap-1.5 rounded-xl px-3 py-1 font-bold">
                        <span
                          className={`inline-block h-2 w-2 rounded-full ${wazuhConnected ? 'bg-primary-500 animate-pulse' : 'bg-slate-400 animate-pulse'}`}
                        />
                        {wazuhConnected ? 'Connected' : wazuhConfigured ? 'Offline' : 'Not Configured'}
                      </Badge>
                    </div>
                    {wazuhConfigured ? (
                      <div className="space-y-2">
                        <p className="text-xs text-slate-700 dark:text-slate-350 font-semibold">
                          Connected to: <span className="font-mono text-[11px] text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">{wazuhHost}:{wazuhPort}</span>
                        </p>
                        <div className="flex items-center gap-2">
                          <Button size="sm" className="rounded-xl font-extrabold shadow-sm bg-indigo-600 text-white" onClick={async () => {
                            if (!selectedOrgId) return;
                            setBusy(true); setError(''); setNotice('');
                            try {
                              const status = await getWazuhAgentStatus(selectedOrgId);
                              setWazuhConnected(status.disconnection_rate <= 10);
                              setNotice(`Agents: ${status.active_agents}/${status.total_agents} active (${status.disconnection_rate}% disconnected)`);
                            } catch (err) {
                              const msg = (err as Error).message || '';
                              if (msg.includes('action_required') || msg.includes('Wazuh not configured')) {
                                setWazuhConfigured(false);
                                setError('Wazuh not configured. Connect your SOC Lab.');
                              } else {
                                setError(msg || 'Failed to query Wazuh');
                              }
                            }
                            setBusy(false);
                          }} disabled={busy || !selectedOrgId}>{busy ? 'Querying...' : 'Fetch Live Telemetry'}</Button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <Input label="Manager Host" value={wazuhHost} onChange={(e) => setWazuhHost(e.target.value)} placeholder="wazuh.local" />
                        <Input label="Port" value={String(wazuhPort)} onChange={(e) => setWazuhPort(Number(e.target.value))} placeholder="55000" />
                        <Input label="API Key / Password" value={wazuhApiKey} onChange={(e) => setWazuhApiKey(e.target.value)} placeholder="secret" />
                        <div className="flex items-center gap-2 pt-1">
                          <Button size="sm" className="rounded-xl font-extrabold bg-indigo-650 hover:bg-indigo-700 text-white shadow-sm" onClick={async () => {
                            if (!selectedOrgId) return; setBusy(true); setError(''); setNotice('');
                            try {
                              await configureWazuh({ org_id: selectedOrgId, wazuh_host: wazuhHost, wazuh_api_key: wazuhApiKey, wazuh_port: Number(wazuhPort) });
                              setWazuhSyncing(true);
                            } catch (err) { setError((err as Error).message || 'Failed to configure Wazuh'); }
                            setBusy(false);
                          }} disabled={busy || !selectedOrgId || isReadOnly}>Connect Wazuh</Button>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Splunk MCP Ingestion Tab */}
        {activeTab === 'splunk' && (
          <div className="space-y-6">
            <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-slate-105 font-extrabold text-base flex items-center gap-2">
                  <Database className="h-5 w-5 text-indigo-500" />
                  Splunk MCP Connector
                </CardTitle>
                <CardDescription className="text-xs font-semibold">
                  Connect your Splunk instance for evidence-based security verification, or seed synthetic findings for demos.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* HEC Configuration */}
                <div className="p-4 border border-slate-200/60 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">Splunk MCP configuration</h3>
                    {splunkConfigured && (
                      <Badge variant="success" className="gap-1.5 rounded-xl px-2.5 py-1 font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Configured
                      </Badge>
                    )}
                  </div>
                  {splunkConfigured ? (
                    <div className="space-y-2">
                      <p className="text-xs text-slate-700 dark:text-slate-350 font-semibold">
                        Connected to: <span className="font-mono text-[11px] text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">{splunkConfigUrl}</span>
                      </p>
                      <div className="flex items-center gap-2">
                        <Button size="sm" className="rounded-xl font-extrabold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm" onClick={handlePullEvidence} disabled={busy || evidenceLoading || !selectedOrgId}>
                          {evidenceLoading ? 'Pulling Evidence...' : 'Pull Live Evidence'}
                        </Button>
                        {!isReadOnly && (
                          <Button size="sm" variant="outline" className="rounded-xl font-bold text-red-500 hover:text-red-600 shadow-sm" onClick={handleRemoveSplunkConfig} disabled={busy}>
                            Disconnect
                          </Button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <Input
                        label="Splunk URL"
                        value={splunkBaseUrl}
                        onChange={(e) => setSplunkBaseUrl(e.target.value)}
                        placeholder="https://splunk.example.com:8089"
                      />
                      <Input
                        label="MCP Token"
                        value={splunkHecToken}
                        onChange={(e) => setSplunkHecToken(e.target.value)}
                        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      />
                      <div className="pt-1">
                        <Button
                          size="sm"
                          className="rounded-xl font-extrabold bg-indigo-650 hover:bg-indigo-700 text-white shadow-sm"
                          onClick={handleconfigureSplunkMcp}
                          disabled={busy || !selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim() || isReadOnly}
                        >
                          Connect Splunk MCP
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Evidence Health Check Results */}
                {evidenceResults && (
                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">Evidence Health Check results</h3>
                      <Badge variant={evidenceResults.overall_status === 'verified' ? 'success' : 'outline'} className="rounded-xl px-2.5 py-1 font-bold">
                        {evidenceResults.verified_controls}/{evidenceResults.total_controls} Controls Verified
                      </Badge>
                    </div>
                    <div className="space-y-2.5">
                      {evidenceResults.results.map((result, idx) => (
                        <div
                          key={idx}
                          className={`p-3.5 rounded-2xl border ${
                            result.status === 'verified'
                              ? 'border-green-200 dark:border-green-900/40 bg-green-50/10 dark:bg-green-950/10'
                              : result.status === 'partial'
                              ? 'border-amber-250 dark:border-amber-900/40 bg-amber-50/10 dark:bg-amber-950/10'
                              : 'border-red-200 dark:border-red-900/40 bg-red-50/10 dark:bg-red-950/10'
                          } transition-all`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-extrabold text-slate-900 dark:text-slate-100">{result.control}</span>
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold">
                              {result.status === 'verified' ? (
                                <span className="text-green-700 dark:text-green-400 flex items-center gap-1">
                                  <ShieldCheck className="w-4 h-4" />
                                  Verified via Splunk
                                </span>
                              ) : result.status === 'partial' ? (
                                <span className="text-amber-700 dark:text-amber-400">Partial Evidence</span>
                              ) : result.status === 'not_configured' ? (
                                <span className="text-slate-500 dark:text-slate-400">Not Configured</span>
                              ) : (
                                <span className="text-red-750 dark:text-red-400 font-extrabold">Not Verified</span>
                              )}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-semibold">{result.message}</p>
                          {result.event_count > 0 && (
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 font-bold">{result.event_count} events found</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Mock Seed / External Findings */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200/50 dark:border-slate-800/40">
                  <Badge variant={splunkConnected ? 'success' : 'outline'} className="rounded-xl px-2.5 py-1 font-bold">
                    {splunkConnected ? 'Findings Synced' : 'No Findings'}
                  </Badge>
                  {!isReadOnly && (
                    <>
                      <Button size="sm" className="rounded-xl font-extrabold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm" onClick={handleConnectSplunk} disabled={busy || !selectedOrgId}>
                        Seed Mock Findings
                      </Button>
                      <Button size="sm" variant="outline" className="rounded-xl font-extrabold shadow-sm" onClick={handleSeedFindings} disabled={busy || !selectedOrgId}>
                        Add More Findings
                      </Button>
                    </>
                  )}
                </div>

                <div className="overflow-x-auto border border-slate-200 dark:border-slate-800/60 rounded-2xl">
                  <table className="min-w-full text-xs">
                    <thead className="bg-slate-50/50 dark:bg-slate-900/30 border-b border-slate-200 dark:border-slate-800">
                      <tr className="text-slate-500 font-bold uppercase tracking-wider">
                        <th className="text-left px-4 py-3">Timestamp</th>
                        <th className="text-left px-4 py-3">Severity</th>
                        <th className="text-left px-4 py-3">Title</th>
                        <th className="text-left px-4 py-3">Source</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono">
                      {externalFindings.length === 0 && (
                        <tr>
                          <td className="px-4 py-6 text-slate-500 dark:text-slate-450 italic font-semibold text-center font-sans" colSpan={4}>
                            No ingested findings yet.
                          </td>
                        </tr>
                      )}
                      {externalFindings.map((finding) => (
                        <tr key={finding.id} className="border-b border-slate-105 dark:border-slate-800/65 hover:bg-slate-50/60 dark:hover:bg-slate-900/20 transition-colors">
                          <td className="px-4 py-3 text-slate-650 dark:text-slate-400 font-semibold">{new Date(finding.created_at).toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <Badge variant="outline" className="rounded-xl px-2 py-0.5 font-bold border-slate-300 dark:border-slate-700">{finding.severity}</Badge>
                          </td>
                          <td className="px-4 py-3 text-slate-905 dark:text-slate-100 font-extrabold font-sans">{finding.title}</td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                            <span className="inline-flex items-center gap-1.5 font-sans font-semibold">
                              <Database className="w-3.5 h-3.5" />
                              {finding.source}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* API Webhooks Gateway Tab */}
        {activeTab === 'webhooks' && (
          <div className="space-y-6">
            {newKey && (
              <Card className="border-blue-200 dark:border-blue-800/40 bg-blue-50/10 dark:bg-blue-950/10 shadow-sm hover:shadow-md">
                <CardHeader>
                  <CardTitle className="text-blue-900 dark:text-blue-300 font-extrabold text-base">New API Key (Copy Once)</CardTitle>
                  <CardDescription className="text-xs text-blue-800/80 dark:text-blue-400 font-semibold">
                    This value is shown once. Save it now.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <code className="block text-xs bg-white dark:bg-slate-950 border border-blue-200/50 dark:border-blue-900/30 rounded-xl p-3.5 overflow-x-auto font-mono text-slate-900 dark:text-slate-100 font-bold shadow-inner">
                    {newKey.api_key}
                  </code>
                  <Button size="sm" onClick={handleCopy} className="gap-2 rounded-xl font-bold">
                    {copied ? <CheckCircle2 className="w-4 h-4 text-[#00C853]" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied' : 'Copy key'}
                  </Button>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* API Access Keys */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-slate-100 font-extrabold text-base flex items-center gap-2">
                    <KeyRound className="h-5 w-5 text-indigo-500" />
                    API Access Keys
                  </CardTitle>
                  <CardDescription className="text-xs font-semibold">Use keys for pull-based integrations (SIEM, dashboards).</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-700 dark:text-slate-350 font-bold">Org: {selectedOrgName}</span>
                    {!isReadOnly && (
                      <Button size="sm" className="rounded-xl font-extrabold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm" onClick={handleCreateApiKey} disabled={busy || !selectedOrgId}>
                        Generate New Key
                      </Button>
                    )}
                  </div>
                  <div className="space-y-2">
                    {apiKeys.length === 0 && <p className="text-xs text-slate-500 dark:text-slate-400 italic font-semibold">No API keys registered yet.</p>}
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-3.5 border border-slate-250 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                      >
                        <div>
                          <div className="text-xs font-bold text-slate-900 dark:text-slate-100 font-mono">{key.prefix}...</div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold mt-0.5">{new Date(key.created_at).toLocaleString()}</div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-xl font-extrabold text-red-500 hover:text-red-650"
                          onClick={() => handleRevokeApiKey(key.id)}
                          disabled={busy || !key.is_active || isReadOnly}
                        >
                          Revoke
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Webhooks Gateway */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-slate-100 font-extrabold text-base flex items-center gap-2">
                    <WebhookIcon className="h-5 w-5 text-indigo-500" />
                    Webhooks Ingestion Gateway
                  </CardTitle>
                  <CardDescription className="text-xs font-semibold">Push assessment-scored events to your tooling.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <Input
                      label="Webhook URL"
                      value={webhookUrl}
                      onChange={(e) => setWebhookUrl(e.target.value)}
                      placeholder="https://example.com/resilai-events"
                    />
                    <Input
                      label="Signing Secret (Optional)"
                      value={webhookSecret}
                      onChange={(e) => setWebhookSecret(e.target.value)}
                      placeholder="webhook secret"
                    />
                  </div>
                  <div className="flex items-center gap-2 pt-1">
                    <Badge variant="outline" className="rounded-xl px-2.5 py-1 font-bold border-slate-300 dark:border-slate-700 text-[10px]">assessment.scored</Badge>
                    {!isReadOnly && (
                      <Button size="sm" className="rounded-xl font-extrabold bg-indigo-650 hover:bg-indigo-750 text-white shadow-sm" onClick={handleCreateWebhook} disabled={busy || !selectedOrgId || !webhookUrl.trim()}>
                        Add Webhook
                      </Button>
                    )}
                  </div>

                  <div className="space-y-2 pt-2">
                    {webhooks.length === 0 && <p className="text-xs text-slate-500 dark:text-slate-400 italic font-semibold">No webhooks configured.</p>}
                    {webhooks.map((hook) => (
                      <div key={hook.id} className="p-3.5 border border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-2">
                        <div className="text-xs font-bold text-slate-900 dark:text-slate-100 break-all font-mono">{hook.url}</div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="outline" className="rounded-xl font-bold shadow-sm" onClick={() => handleTestWebhook(hook.id)} disabled={busy}>
                            Run Check
                          </Button>
                          {!isReadOnly && (
                            <Button size="sm" variant="outline" className="rounded-xl font-bold text-red-500 hover:text-red-650 shadow-sm" onClick={() => handleDeleteWebhook(hook.id)} disabled={busy}>
                              Disable
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-4 border-t border-slate-200 dark:border-slate-800/85 space-y-3">
                    <Input
                      label="Quick Webhook Check URL"
                      value={webhookTestUrl}
                      onChange={(e) => setWebhookTestUrl(e.target.value)}
                      placeholder="https://webhook.site/your-check-id"
                    />
                    <div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-xl font-extrabold shadow-sm"
                        onClick={handleTestWebhookUrl}
                        disabled={busy || !webhookTestUrl.trim()}
                      >
                        Send Check
                      </Button>
                    </div>
                    {webhookTestResult && <p className="text-xs text-slate-900 dark:text-slate-100 font-bold">{webhookTestResult}</p>}
                    {webhookTestPayload && (
                      <pre className="text-[10px] bg-slate-50/50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3 overflow-x-auto font-mono text-slate-800 dark:text-slate-200">
                        {webhookTestPayload}
                      </pre>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default EvidenceNetwork;
