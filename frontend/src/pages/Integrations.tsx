import { useEffect, useMemo, useState } from 'react';
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
} from '../api';
import type {
  ApiKeyMetadata,
  ApiKeyCreateResponse,
  ExternalFinding,
  Organization,
  Webhook,
} from '../types';
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
    return <div className="text-sm text-gray-500">Loading integrations...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <ShieldCheck className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-sm text-gray-500">
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
          <Select
            label="Organization"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            options={organizations.map((o) => ({ value: o.id, label: o.name }))}
          />
        </CardContent>
      </Card>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{error}</div>
      )}
      {notice && (
        <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700">
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
            <div className="p-3 border border-gray-200 rounded-lg">
              <div className="text-xs text-gray-500">Splunk</div>
              <div className="mt-1 font-medium text-gray-900">{splunkConnected ? 'Connected' : 'Not Connected'}</div>
            </div>
            <div className="p-3 border border-gray-200 rounded-lg">
              <div className="text-xs text-gray-500">Webhook</div>
              <div className="mt-1 font-medium text-gray-900">{webhooks.length > 0 ? 'Active' : 'Inactive'}</div>
            </div>
            <div className="p-3 border border-gray-200 rounded-lg">
              <div className="text-xs text-gray-500">API Access</div>
              <div className="mt-1 font-medium text-gray-900">{apiKeys.some((k) => k.is_active) ? 'Enabled' : 'Not Enabled'}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {newKey && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-blue-900">New API Key (Copy Once)</CardTitle>
            <CardDescription className="text-blue-800">
              This value is shown once. Save it now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <code className="block text-xs bg-white border border-blue-200 rounded p-3 overflow-x-auto">
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
              <span className="text-sm text-gray-600">Org: {selectedOrgName}</span>
              <Button size="sm" onClick={handleCreateApiKey} disabled={busy || !selectedOrgId}>
                Generate New Key
              </Button>
            </div>
            <div className="space-y-2">
              {apiKeys.length === 0 && <p className="text-sm text-gray-500">No API keys yet.</p>}
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                >
                  <div>
                    <div className="text-sm font-medium text-gray-900">{key.prefix}...</div>
                    <div className="text-xs text-gray-500">{new Date(key.created_at).toLocaleString()}</div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleRevokeApiKey(key.id)}
                    disabled={busy || !key.is_active}
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
              <Button size="sm" onClick={handleCreateWebhook} disabled={busy || !selectedOrgId || !webhookUrl.trim()}>
                Add Webhook
              </Button>
            </div>

            <div className="space-y-2 pt-2">
              {webhooks.length === 0 && <p className="text-sm text-gray-500">No webhooks configured.</p>}
              {webhooks.map((hook) => (
                <div key={hook.id} className="p-3 border border-gray-200 rounded-lg space-y-2">
                  <div className="text-sm font-medium text-gray-900 break-all">{hook.url}</div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleTestWebhook(hook.id)} disabled={busy}>
                      Run Check
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleDeleteWebhook(hook.id)} disabled={busy}>
                      Disable
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-gray-200 space-y-2">
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
              {webhookTestResult && <p className="text-xs text-gray-600">{webhookTestResult}</p>}
              {webhookTestPayload && (
                <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto">
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
            Seed realistic synthetic external findings into ResilAI for integration previews.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={splunkConnected ? 'default' : 'outline'}>
              {splunkConnected ? 'Connected' : 'Not Connected'}
            </Badge>
            <Button size="sm" onClick={handleConnectSplunk} disabled={busy || !selectedOrgId}>
              Connect Splunk
            </Button>
            <Button size="sm" variant="outline" onClick={handleSeedFindings} disabled={busy || !selectedOrgId}>
              Seed Example Findings
            </Button>
            <Button size="sm" variant="outline" onClick={reload} disabled={busy || !selectedOrgId} className="gap-2">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>

          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-3 py-2 font-medium text-gray-600">Timestamp</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600">Severity</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600">Title</th>
                  <th className="text-left px-3 py-2 font-medium text-gray-600">Source</th>
                </tr>
              </thead>
              <tbody>
                {externalFindings.length === 0 && (
                  <tr>
                    <td className="px-3 py-3 text-gray-500" colSpan={4}>
                      No ingested findings yet.
                    </td>
                  </tr>
                )}
                {externalFindings.map((finding) => (
                  <tr key={finding.id} className="border-t border-gray-100">
                    <td className="px-3 py-2 text-gray-600">{new Date(finding.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2">
                      <Badge variant="outline">{finding.severity}</Badge>
                    </td>
                    <td className="px-3 py-2 text-gray-900">{finding.title}</td>
                    <td className="px-3 py-2 text-gray-600">
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
