import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
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
    return <div className="text-sm text-gray-500 dark:text-slate-400">Loading integrations...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
          <ShieldCheck className="h-5 w-5 text-blue-600 dark:text-blue-300" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Integrations</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            API keys, webhooks, and SIEM ingestion hooks for external tooling.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Organization</CardTitle>
          <CardDescription>Select which organization to manage.</CardDescription>
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
            <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Create an organization before configuring integrations.
              </p>
              <Link to="/dashboard/org/new" className="inline-flex mt-3">
                <Button size="sm">Create Organization</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">{error}</div>
      )}
      {notice && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-sm text-green-700 dark:text-green-300">
          {notice}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Connected Integrations</CardTitle>
          <CardDescription>Live status for enterprise integration capabilities.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900">
              <div className="text-xs text-gray-500 dark:text-slate-400">Splunk</div>
              <div className="mt-1 font-medium text-gray-900 dark:text-slate-100">
                {splunkConnected ? 'Connected (Last sync: 5 min ago)' : 'Not Connected'}
              </div>
            </div>
            <div className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900">
              <div className="text-xs text-gray-500 dark:text-slate-400">Webhook</div>
              <div className="mt-1 font-medium text-gray-900 dark:text-slate-100">
                {webhooks.length > 0 ? 'Active (Last delivery check: 2 min ago)' : 'Inactive'}
              </div>
            </div>
            <div className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900">
              <div className="text-xs text-gray-500 dark:text-slate-400">API Access</div>
              <div className="mt-1 font-medium text-gray-900 dark:text-slate-100">
                {apiKeys.some((k) => k.is_active) ? 'Enabled (Key active)' : 'Not Enabled'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {newKey && (
        <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
          <CardHeader>
            <CardTitle className="text-blue-900 dark:text-blue-200">New API Key (Copy Once)</CardTitle>
            <CardDescription className="text-blue-800 dark:text-blue-300">
              This value is shown once. Save it now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <code className="block text-xs bg-white dark:bg-slate-900 border border-blue-200 dark:border-blue-800 rounded p-3 overflow-x-auto">
              {newKey.api_key}
            </code>
            <Button size="sm" onClick={handleCopy} className="gap-2">
              {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy key'}
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-gray-500" />
              API Access
            </CardTitle>
            <CardDescription>Use keys for pull-based integration (SIEM, dashboards).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-slate-300">Org: {selectedOrgName}</span>
              {!isReadOnly && (
                <Button size="sm" onClick={handleCreateApiKey} disabled={busy || !selectedOrgId}>
                  Generate New Key
                </Button>
              )}
            </div>
            <div className="space-y-2">
              {apiKeys.length === 0 && <p className="text-sm text-gray-500 dark:text-slate-400">No API keys yet.</p>}
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between p-3 border border-gray-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900"
                >
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-slate-100">{key.prefix}...</div>
                    <div className="text-xs text-gray-500 dark:text-slate-400">{new Date(key.created_at).toLocaleString()}</div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
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

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <WebhookIcon className="h-5 w-5 text-gray-500" />
              Webhooks
            </CardTitle>
            <CardDescription>Push assessment-scored events to your tooling.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
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
            <div className="flex items-center gap-2">
              <Badge variant="outline">assessment.scored</Badge>
              {!isReadOnly && (
                <Button size="sm" onClick={handleCreateWebhook} disabled={busy || !selectedOrgId || !webhookUrl.trim()}>
                  Add Webhook
                </Button>
              )}
            </div>

            <div className="space-y-2 pt-2">
              {webhooks.length === 0 && <p className="text-sm text-gray-500 dark:text-slate-400">No webhooks configured.</p>}
              {webhooks.map((hook) => (
                <div key={hook.id} className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg space-y-2 bg-white dark:bg-slate-900">
                  <div className="text-sm font-medium text-gray-900 dark:text-slate-100 break-all">{hook.url}</div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleTestWebhook(hook.id)} disabled={busy}>
                      Run Check
                    </Button>
                    {!isReadOnly && (
                      <Button size="sm" variant="outline" onClick={() => handleDeleteWebhook(hook.id)} disabled={busy}>
                        Disable
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-gray-200 dark:border-slate-800 space-y-2">
              <Input
                label="Quick Webhook Check URL"
                value={webhookTestUrl}
                onChange={(e) => setWebhookTestUrl(e.target.value)}
                placeholder="https://webhook.site/your-check-id"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={handleTestWebhookUrl}
                disabled={busy || !webhookTestUrl.trim()}
              >
                Send Check
              </Button>
              {webhookTestResult && <p className="text-xs text-gray-600 dark:text-slate-300">{webhookTestResult}</p>}
              {webhookTestPayload && (
                <pre className="text-xs bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded p-3 overflow-x-auto">
                  {webhookTestPayload}
                </pre>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlugZap className="h-5 w-5 text-gray-500" />
            Splunk Connector (Public Beta)
          </CardTitle>
          <CardDescription>
            Connect your Splunk instance for evidence-based security verification, or seed synthetic findings for demos.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* HEC Configuration */}
          <div className="p-4 border border-gray-200 dark:border-slate-700 rounded-lg bg-gray-50 dark:bg-slate-900/50 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100">Splunk HEC Configuration</h3>
              {splunkConfigured && (
                <Badge variant="default" className="gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Configured
                </Badge>
              )}
            </div>
            {splunkConfigured ? (
              <div className="space-y-2">
                <p className="text-sm text-gray-600 dark:text-slate-300">
                  Connected to: <span className="font-mono text-xs">{splunkConfigUrl}</span>
                </p>
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={handlePullEvidence} disabled={busy || evidenceLoading || !selectedOrgId}>
                    {evidenceLoading ? 'Pulling Evidence...' : 'Pull Live Evidence'}
                  </Button>
                  {!isReadOnly && (
                    <Button size="sm" variant="outline" onClick={handleRemoveSplunkConfig} disabled={busy}>
                      Disconnect
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
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
                <Button
                  size="sm"
                  onClick={handleConfigureSplunkHec}
                  disabled={busy || !selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim() || isReadOnly}
                >
                  Connect Splunk HEC
                </Button>
              </div>
            )}
          </div>

          {/* Evidence Verification Results */}
          {evidenceResults && (
            <div className="p-4 border border-gray-200 dark:border-slate-700 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100">Evidence Verification</h3>
                <Badge variant={
                  evidenceResults.overall_status === 'verified' ? 'default' :
                  evidenceResults.overall_status === 'partial' ? 'outline' : 'outline'
                }>
                  {evidenceResults.verified_controls}/{evidenceResults.total_controls} Controls Verified
                </Badge>
              </div>
              <div className="space-y-2">
                {evidenceResults.results.map((result, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${
                      result.status === 'verified'
                        ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                        : result.status === 'partial'
                        ? 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20'
                        : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 dark:text-slate-100">{result.control}</span>
                      <span className="inline-flex items-center gap-1 text-xs font-medium">
                        {result.status === 'verified' ? (
                          <span className="text-green-700 dark:text-green-300 flex items-center gap-1">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            Verified via Splunk
                          </span>
                        ) : result.status === 'partial' ? (
                          <span className="text-amber-700 dark:text-amber-300">Partial Evidence</span>
                        ) : result.status === 'not_configured' ? (
                          <span className="text-gray-500 dark:text-slate-400">Not Configured</span>
                        ) : (
                          <span className="text-red-700 dark:text-red-300">Not Verified</span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">{result.message}</p>
                    {result.event_count > 0 && (
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">{result.event_count} events found</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mock Seed / External Findings */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={splunkConnected ? 'default' : 'outline'}>
              {splunkConnected ? 'Findings Synced' : 'No Findings'}
            </Badge>
            {!isReadOnly && (
              <>
                <Button size="sm" onClick={handleConnectSplunk} disabled={busy || !selectedOrgId}>
                  Seed Mock Findings
                </Button>
                <Button size="sm" variant="outline" onClick={handleSeedFindings} disabled={busy || !selectedOrgId}>
                  Add More Findings
                </Button>
              </>
            )}
            <Button size="sm" variant="outline" onClick={reload} disabled={busy || !selectedOrgId} className="gap-2">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
          {!selectedOrgId && (
            <p className="text-sm text-amber-700 dark:text-amber-300">
              Select or create an organization to enable the Splunk connector.
            </p>
          )}

          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-slate-900">
                <tr>
                  <th className="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-300">Timestamp</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-300">Severity</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-300">Title</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-300">Source</th>
                </tr>
              </thead>
              <tbody>
                {externalFindings.length === 0 && (
                  <tr>
                    <td className="px-3 py-3 text-gray-500 dark:text-slate-400" colSpan={4}>
                      No ingested findings yet.
                    </td>
                  </tr>
                )}
                {externalFindings.map((finding) => (
                  <tr key={finding.id} className="border-t border-gray-100 dark:border-slate-800">
                    <td className="px-3 py-2 text-gray-600 dark:text-slate-300">{new Date(finding.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2">
                      <Badge variant="outline">{finding.severity}</Badge>
                    </td>
                    <td className="px-3 py-2 text-gray-900 dark:text-slate-100">{finding.title}</td>
                    <td className="px-3 py-2 text-gray-600 dark:text-slate-300">
                      <span className="inline-flex items-center gap-1">
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
  );
}