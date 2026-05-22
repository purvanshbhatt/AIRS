import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useIsReadOnly } from '../contexts';
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
  configureSplunkHec,
  getSplunkConfig,
  removeSplunkConfig,
  pullSplunkEvidence,
  configureWazuh,
  getWazuhAgentStatus,
} from '../api';
import type {
  ApiKeyMetadata,
  ApiKeyCreateResponse,
  ExternalFinding,
  Organization,
  Webhook,
} from '../types';
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
} from 'lucide-react';

export default function Integrations() {
  const isReadOnly = useIsReadOnly();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [apiKeys, setApiKeys] = useState<ApiKeyMetadata[]>([]);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [externalFindings, setExternalFindings] = useState<ExternalFinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [splunkConnected, setSplunkConnected] = useState(false);

  const [newKey, setNewKey] = useState<ApiKeyCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [webhookTestUrl, setWebhookTestUrl] = useState('');
  const [webhookTestResult, setWebhookTestResult] = useState('');
  const [webhookTestPayload, setWebhookTestPayload] = useState('');

  // Splunk HEC configuration
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
  const [evidenceResults, setEvidenceResults] = useState<SplunkEvidenceResponse | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);

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

  useEffect(() => {
    if (!selectedOrgId) return;
    const run = async () => {
      setError('');
      try {
        const [keys, hooks, findings] = await Promise.all([
          listApiKeys(selectedOrgId),
          listWebhooks(selectedOrgId),
          getExternalFindings({ source: 'splunk', limit: 50, orgId: selectedOrgId }),
        ]);
        setApiKeys(keys);
        setWebhooks(hooks);
        setExternalFindings(findings);
        setSplunkConnected(findings.length > 0);
        // Check if Splunk HEC is configured
        try {
          const cfg = await getSplunkConfig(selectedOrgId);
          setSplunkConfigured(cfg.configured);
          setSplunkConfigUrl(cfg.base_url || '');
        } catch {
          setSplunkConfigured(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load integrations');
      }
    };
    run();
  }, [selectedOrgId]);

  const reload = async () => {
    if (!selectedOrgId) return;
    const [keys, hooks, findings] = await Promise.all([
      listApiKeys(selectedOrgId),
      listWebhooks(selectedOrgId),
      getExternalFindings({ source: 'splunk', limit: 50, orgId: selectedOrgId }),
    ]);
    setApiKeys(keys);
    setWebhooks(hooks);
    setExternalFindings(findings);
    setSplunkConnected(findings.length > 0);
  };

  const handleCreateApiKey = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const created = await createApiKey(selectedOrgId, ['scores:read']);
      setNewKey(created);
      setCopied(false);
      await reload();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage());
      } else {
        setError(err instanceof Error ? err.message : 'Failed to create API key');
      }
    } finally {
      setBusy(false);
    }
  };

  const handleCopy = async () => {
    if (!newKey?.api_key) return;
    await navigator.clipboard.writeText(newKey.api_key);
    setCopied(true);
  };

  const handleRevokeApiKey = async (id: string) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await revokeApiKey(id);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key');
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
        event_types: ['assessment.scored'],
        secret: webhookSecret.trim() || undefined,
      });
      setWebhookUrl('');
      setWebhookSecret('');
      await reload();
      setNotice('Webhook created.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create webhook');
    } finally {
      setBusy(false);
    }
  };

  const handleTestWebhook = async (id: string) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await testWebhook(id);
      if (!result.delivered) {
        setError(result.error || `Delivery check failed (HTTP ${result.status_code || 'unknown'})`);
      } else {
        setNotice(`Webhook delivery check succeeded (HTTP ${result.status_code || 200}).`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run webhook delivery check');
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

  const handleConfigureSplunkHec = async () => {
    if (!selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await configureSplunkHec(selectedOrgId, splunkBaseUrl.trim(), splunkHecToken.trim());
      setSplunkConfigured(true);
      setSplunkConfigUrl(splunkBaseUrl.trim());
      setSplunkHecToken('');
      setNotice('Splunk HEC configured successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to configure Splunk HEC');
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
      setNotice('Splunk HEC configuration removed.');
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
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-center py-20 text-sm text-slate-505 dark:text-slate-455 font-bold"
      >
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading integrations...
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="max-w-6xl mx-auto space-y-6"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-blue-55/10 dark:bg-blue-955/20 border border-blue-200 dark:border-blue-900/40 flex items-center justify-center">
          <ShieldCheck className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-150 tracking-tight">Integrations</h1>
          <p className="text-sm text-slate-505 dark:text-slate-455 font-semibold">
            API keys, webhooks, and SIEM ingestion hooks for external tooling.
          </p>
        </div>
      </div>

      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-slate-155 font-extrabold text-lg">Organization</CardTitle>
          <CardDescription className="text-slate-500 dark:text-slate-455 font-semibold">Select which organization to manage.</CardDescription>
        </CardHeader>
        <CardContent>
          {organizations.length > 0 ? (
            <Select
              label="Organization"
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
              options={organizations.map((o) => ({ value: o.id, label: o.name }))}
            />
          ) : (
            <div className="rounded-2xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-955/10 p-4">
              <p className="text-sm text-amber-800 dark:text-amber-300 font-bold">
                Create an organization before configuring integrations.
              </p>
              <Link to="/dashboard/org/new" className="inline-flex mt-3">
                <Button size="sm" className="rounded-xl font-extrabold shadow-sm">Create Organization</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Wazuh Connector Card */}
      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-slate-150 font-extrabold text-lg flex items-center gap-2">
            <PlugZap className="h-5 w-5 text-slate-500 dark:text-slate-400" />
            Wazuh Connector (Lab)
          </CardTitle>
          <CardDescription className="text-slate-505 dark:text-slate-455 font-semibold">
            Connect a Wazuh manager to pull agent status and vulnerability telemetry.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-150">Wazuh Manager</h3>
              <Badge variant={wazuhConnected ? 'default' : 'outline'} className="gap-1.5 rounded-xl px-3 py-1 font-bold">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${wazuhConnected ? 'bg-blue-500 animate-pulse' : 'bg-red-500 animate-pulse'}`}
                />
                {wazuhConnected ? 'Connected' : wazuhConfigured ? 'Offline' : 'Not Configured'}
              </Badge>
            </div>
            {wazuhConfigured ? (
              <div className="space-y-2">
                <p className="text-sm text-slate-700 dark:text-slate-300 font-semibold">
                  Connected to: <span className="font-mono text-xs text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">{wazuhHost}:{wazuhPort}</span>
                </p>
                <div className="flex items-center gap-2">
                  <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={async () => {
                    if (!selectedOrgId) return;
                    setBusy(true); setError(''); setNotice('');
                    try {
                      const status = await getWazuhAgentStatus();
                      setWazuhConnected(status.disconnection_rate <= 10);
                      setNotice(`Agents: ${status.active_agents}/${status.total_agents} active (${status.disconnection_rate}% disconnected)`);
                    } catch (err) { setError((err as Error).message || 'Failed to query Wazuh'); }
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
                  <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={async () => {
                    if (!selectedOrgId) return; setBusy(true); setError(''); setNotice('');
                    try {
                      await configureWazuh({ wazuh_host: wazuhHost, wazuh_api_key: wazuhApiKey, wazuh_port: Number(wazuhPort) });
                      setWazuhConfigured(true);
                      setNotice('Wazuh configured successfully.');
                    } catch (err) { setError((err as Error).message || 'Failed to configure Wazuh'); }
                    setBusy(false);
                  }} disabled={busy || !selectedOrgId || isReadOnly}>Connect Wazuh</Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="p-3.5 bg-red-50/20 dark:bg-red-955/10 border border-red-200 dark:border-red-900/40 rounded-2xl text-sm text-red-700 dark:text-red-400 font-semibold shadow-sm">{error}</div>
      )}
      {notice && (
        <div className="p-3.5 bg-green-50/20 dark:bg-green-955/10 border border-green-200 dark:border-green-900/40 rounded-2xl text-sm text-green-750 dark:text-green-400 font-semibold shadow-sm">
          {notice}
        </div>
      )}

      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-slate-155 font-extrabold text-lg">Connected Integrations</CardTitle>
          <CardDescription className="text-slate-505 dark:text-slate-455 font-semibold">Live status for enterprise integration capabilities.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all">
              <div className="text-xs text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Splunk</div>
              <div className="mt-1.5 font-extrabold text-slate-900 dark:text-slate-150">
                {splunkConnected ? 'Connected (Last sync: 5 min ago)' : 'Not Connected'}
              </div>
            </div>
            <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all">
              <div className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">Webhook</div>
              <div className="mt-1.5 font-extrabold text-slate-900 dark:text-slate-150">
                {webhooks.length > 0 ? 'Active (Last delivery check: 2 min ago)' : 'Inactive'}
              </div>
            </div>
            <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all">
              <div className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">API Access</div>
              <div className="mt-1.5 font-extrabold text-slate-900 dark:text-slate-150">
                {apiKeys.some((k) => k.is_active) ? 'Enabled (Key active)' : 'Not Enabled'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {newKey && (
        <Card className="rounded-3xl border border-blue-200 dark:border-blue-800/40 bg-blue-50/10 dark:bg-blue-955/10 shadow-sm transition-all duration-300">
          <CardHeader>
            <CardTitle className="text-blue-900 dark:text-blue-300 font-extrabold text-lg">New API Key (Copy Once)</CardTitle>
            <CardDescription className="text-blue-800/80 dark:text-blue-400 font-semibold">
              This value is shown once. Save it now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <code className="block text-xs bg-white dark:bg-slate-950 border border-blue-200/50 dark:border-blue-900/30 rounded-xl p-3.5 overflow-x-auto font-mono text-slate-900 dark:text-slate-150 font-bold shadow-inner">
              {newKey.api_key}
            </code>
            <Button size="sm" onClick={handleCopy} className="gap-2 rounded-xl font-bold shadow-sm">
              {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy key'}
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-slate-150 font-extrabold text-lg flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-slate-500 dark:text-slate-400" />
              API Access
            </CardTitle>
            <CardDescription className="text-slate-505 dark:text-slate-455 font-semibold">Use keys for pull-based integration (SIEM, dashboards).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700 dark:text-slate-305 font-bold">Org: {selectedOrgName}</span>
              {!isReadOnly && (
                <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={handleCreateApiKey} disabled={busy || !selectedOrgId}>
                  Generate New Key
                </Button>
              )}
            </div>
            <div className="space-y-2">
              {apiKeys.length === 0 && <p className="text-sm text-slate-505 dark:text-slate-455 italic font-semibold">No API keys yet.</p>}
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between p-3.5 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                >
                  <div>
                    <div className="text-sm font-bold text-slate-900 dark:text-slate-150 font-mono text-xs">{key.prefix}...</div>
                    <div className="text-xs text-slate-505 dark:text-slate-455 font-semibold mt-0.5">{new Date(key.created_at).toLocaleString()}</div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="rounded-xl font-extrabold shadow-sm"
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

        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-slate-150 font-extrabold text-lg flex items-center gap-2">
              <WebhookIcon className="h-5 w-5 text-slate-500 dark:text-slate-400" />
              Webhooks
            </CardTitle>
            <CardDescription className="text-slate-505 dark:text-slate-455 font-semibold">Push assessment-scored events to your tooling.</CardDescription>
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
              <Badge variant="outline" className="rounded-xl px-2.5 py-1 font-bold border-slate-300 dark:border-slate-700">assessment.scored</Badge>
              {!isReadOnly && (
                <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={handleCreateWebhook} disabled={busy || !selectedOrgId || !webhookUrl.trim()}>
                  Add Webhook
                </Button>
              )}
            </div>

            <div className="space-y-2 pt-2">
              {webhooks.length === 0 && <p className="text-sm text-slate-550 dark:text-slate-400 italic font-semibold">No webhooks configured.</p>}
              {webhooks.map((hook) => (
                <div key={hook.id} className="p-3.5 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-2">
                  <div className="text-sm font-bold text-slate-900 dark:text-slate-150 break-all text-xs font-mono">{hook.url}</div>
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

            <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80 space-y-3">
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
              {webhookTestResult && <p className="text-xs text-slate-900 dark:text-slate-150 font-bold">{webhookTestResult}</p>}
              {webhookTestPayload && (
                <pre className="text-xs bg-slate-50/50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3 overflow-x-auto font-mono text-slate-800 dark:text-slate-200">
                  {webhookTestPayload}
                </pre>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800/60 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-slate-150 font-extrabold text-lg flex items-center gap-2">
            <PlugZap className="h-5 w-5 text-slate-500 dark:text-slate-400" />
            Splunk Connector (Public Beta)
          </CardTitle>
          <CardDescription className="text-slate-505 dark:text-slate-455 font-semibold">
            Connect your Splunk instance for evidence-based security verification, or seed synthetic findings for demos.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* HEC Configuration */}
          <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-150">Splunk HEC Configuration</h3>
              {splunkConfigured && (
                <Badge variant="default" className="gap-1.5 rounded-xl px-2.5 py-1 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Configured
                </Badge>
              )}
            </div>
            {splunkConfigured ? (
              <div className="space-y-2">
                <p className="text-sm text-slate-700 dark:text-slate-300 font-semibold">
                  Connected to: <span className="font-mono text-xs text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">{splunkConfigUrl}</span>
                </p>
                <div className="flex items-center gap-2">
                  <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={handlePullEvidence} disabled={busy || evidenceLoading || !selectedOrgId}>
                    {evidenceLoading ? 'Pulling Evidence...' : 'Pull Live Evidence'}
                  </Button>
                  {!isReadOnly && (
                    <Button size="sm" variant="outline" className="rounded-xl font-bold text-red-500 hover:text-red-650 shadow-sm" onClick={handleRemoveSplunkConfig} disabled={busy}>
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
                  label="HEC Token"
                  value={splunkHecToken}
                  onChange={(e) => setSplunkHecToken(e.target.value)}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                />
                <div className="pt-1">
                  <Button
                    size="sm"
                    className="rounded-xl font-extrabold shadow-sm"
                    onClick={handleConfigureSplunkHec}
                    disabled={busy || !selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim() || isReadOnly}
                  >
                    Connect Splunk HEC
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Evidence Verification Results */}
          {evidenceResults && (
            <div className="p-4 border border-slate-205 dark:border-slate-805 rounded-2xl bg-slate-50/50 dark:bg-slate-950/30 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-150">Evidence Verification</h3>
                <Badge variant={
                  evidenceResults.overall_status === 'verified' ? 'default' : 'outline'
                } className="rounded-xl px-2.5 py-1 font-bold">
                  {evidenceResults.verified_controls}/{evidenceResults.total_controls} Controls Verified
                </Badge>
              </div>
              <div className="space-y-2.5">
                {evidenceResults.results.map((result, idx) => (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl border ${
                      result.status === 'verified'
                        ? 'border-green-200 dark:border-green-900/40 bg-green-50/10 dark:bg-green-955/10'
                        : result.status === 'partial'
                        ? 'border-amber-250 dark:border-amber-900/40 bg-amber-50/10 dark:bg-amber-955/10'
                        : 'border-red-200 dark:border-red-900/40 bg-red-50/10 dark:bg-red-955/10'
                    } transition-all`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-extrabold text-slate-900 dark:text-slate-150">{result.control}</span>
                      <span className="inline-flex items-center gap-1 text-xs font-bold">
                        {result.status === 'verified' ? (
                          <span className="text-green-700 dark:text-green-400 flex items-center gap-1">
                            <ShieldCheck className="w-4 h-4" />
                            Verified via Splunk
                          </span>
                        ) : result.status === 'partial' ? (
                          <span className="text-amber-700 dark:text-amber-400">Partial Evidence</span>
                        ) : result.status === 'not_configured' ? (
                          <span className="text-slate-505 dark:text-slate-455">Not Configured</span>
                        ) : (
                          <span className="text-red-700 dark:text-red-400 font-extrabold">Not Verified</span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-slate-650 dark:text-slate-400 mt-1 font-semibold">{result.message}</p>
                    {result.event_count > 0 && (
                      <p className="text-xs text-slate-500 dark:text-slate-455 mt-1 font-bold">{result.event_count} events found</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mock Seed / External Findings */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={splunkConnected ? 'default' : 'outline'} className="rounded-xl px-2.5 py-1 font-bold">
              {splunkConnected ? 'Findings Synced' : 'No Findings'}
            </Badge>
            {!isReadOnly && (
              <>
                <Button size="sm" className="rounded-xl font-extrabold shadow-sm" onClick={handleConnectSplunk} disabled={busy || !selectedOrgId}>
                  Seed Mock Findings
                </Button>
                <Button size="sm" variant="outline" className="rounded-xl font-extrabold shadow-sm" onClick={handleSeedFindings} disabled={busy || !selectedOrgId}>
                  Add More Findings
                </Button>
              </>
            )}
            <Button size="sm" variant="outline" onClick={reload} disabled={busy || !selectedOrgId} className="gap-2 rounded-xl font-extrabold shadow-sm">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
          {!selectedOrgId && (
            <p className="text-sm text-amber-700 dark:text-amber-400 font-bold">
              Select or create an organization to enable the Splunk connector.
            </p>
          )}

          <div className="overflow-x-auto border border-slate-200 dark:border-slate-800/60 rounded-2xl">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50/50 dark:bg-slate-900/30 border-b border-slate-205 dark:border-slate-805">
                <tr>
                  <th className="text-left px-4 py-3 font-bold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-450">Timestamp</th>
                  <th className="text-left px-4 py-3 font-bold text-xs uppercase tracking-wider text-slate-505 dark:text-slate-455">Severity</th>
                  <th className="text-left px-4 py-3 font-bold text-xs uppercase tracking-wider text-slate-505 dark:text-slate-455">Title</th>
                  <th className="text-left px-4 py-3 font-bold text-xs uppercase tracking-wider text-slate-505 dark:text-slate-455">Source</th>
                </tr>
              </thead>
              <tbody>
                {externalFindings.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-slate-505 dark:text-slate-455 italic font-semibold text-center" colSpan={4}>
                      No ingested findings yet.
                    </td>
                  </tr>
                )}
                {externalFindings.map((finding) => (
                  <tr key={finding.id} className="border-b border-slate-150 dark:border-slate-850/60 hover:bg-slate-50/60 dark:hover:bg-slate-900/20 transition-colors">
                    <td className="px-4 py-3 text-slate-705 dark:text-slate-350 font-semibold">{new Date(finding.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="rounded-xl px-2 py-0.5 font-bold border-slate-300 dark:border-slate-700">{finding.severity}</Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-900 dark:text-slate-150 font-extrabold">{finding.title}</td>
                    <td className="px-4 py-3 text-slate-650 dark:text-slate-400">
                      <span className="inline-flex items-center gap-1.5 font-semibold text-xs text-slate-505 dark:text-slate-455">
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
    </motion.div>
  );
}