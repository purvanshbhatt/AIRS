import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useIsReadOnly } from '../contexts';
import {
  getOrganizations,
  configureSplunkHec,
  getSplunkConfig,
  removeSplunkConfig,
  pullSplunkEvidence,
  configureWazuh,
  getWazuhAgentStatus,
  getIntegrationStatus,
  seedMockSplunkFindings,
  ApiRequestError,
} from '../api';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Input,
  Select,
  Badge,
  useToast,
} from '../components/ui';
import {
  Database,
  Loader2,
  PlugZap,
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Play,
  KeyRound,
  Webhook,
  Zap,
} from 'lucide-react';

export default function NewAssessment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { addToast } = useToast();
  const isReadOnly = useIsReadOnly();

  // Redirect if read-only (optional, but let's allow viewing telemetry config even in read-only, just disable actions)
  const [organizations, setOrganizations] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Wazuh connection state
  const [wazuhHost, setWazuhHost] = useState('');
  const [wazuhPort, setWazuhPort] = useState(55000);
  const [wazuhApiKey, setWazuhApiKey] = useState('');
  const [wazuhConfigured, setWazuhConfigured] = useState(false);
  const [wazuhConnected, setWazuhConnected] = useState(false);
  const [wazuhAgents, setWazuhAgents] = useState<{ active: number; total: number } | null>(null);

  // Splunk config state
  const [splunkBaseUrl, setSplunkBaseUrl] = useState('');
  const [splunkHecToken, setSplunkHecToken] = useState('');
  const [splunkConfigured, setSplunkConfigured] = useState(false);
  const [splunkConfigUrl, setSplunkConfigUrl] = useState('');
  const [splunkEvidenceCount, setSplunkEvidenceCount] = useState<number | null>(null);

  useEffect(() => {
    async function loadOrgs() {
      setLoading(true);
      setError('');
      try {
        const orgs = await getOrganizations();
        setOrganizations(orgs);
        const orgFromQuery = searchParams.get('org');
        if (orgFromQuery && orgs.some((o) => o.id === orgFromQuery)) {
          setSelectedOrgId(orgFromQuery);
        } else if (orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load organizations');
      } finally {
        setLoading(false);
      }
    }
    loadOrgs();
  }, [searchParams]);

  const loadIntegrationStatus = useCallback(async (orgId: string) => {
    if (!orgId) return;
    setError('');
    setNotice('');
    try {
      const [integrationStatus, splunkConfig] = await Promise.all([
        getIntegrationStatus(orgId),
        getSplunkConfig(orgId),
      ]);

      const isWazuhConfigured = integrationStatus.wazuh_status === 'configured';
      setWazuhConfigured(isWazuhConfigured);
      if (isWazuhConfigured) {
        setWazuhHost(integrationStatus.wazuh_host || '');
        setWazuhPort(integrationStatus.wazuh_port || 55000);
        // Try fetching active agent count
        try {
          const agents = await getWazuhAgentStatus(orgId);
          setWazuhConnected(agents.disconnection_rate <= 10);
          setWazuhAgents({ active: agents.active_agents, total: agents.total_agents });
        } catch {
          setWazuhConnected(false);
        }
      } else {
        setWazuhHost('');
        setWazuhPort(55000);
        setWazuhConnected(false);
        setWazuhAgents(null);
      }

      setSplunkConfigured(splunkConfig.configured);
      setSplunkConfigUrl(splunkConfig.base_url || '');
      if (splunkConfig.configured) {
        try {
          const evidence = await pullSplunkEvidence(orgId);
          setSplunkEvidenceCount(evidence.verified_controls);
        } catch {
          setSplunkEvidenceCount(null);
        }
      } else {
        setSplunkBaseUrl('');
        setSplunkEvidenceCount(null);
      }
    } catch (err) {
      setError('Failed to query active integration settings.');
    }
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      loadIntegrationStatus(selectedOrgId);
    }
  }, [selectedOrgId, loadIntegrationStatus]);

  const handleConfigureWazuh = async () => {
    if (!selectedOrgId || !wazuhHost.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await configureWazuh({
        org_id: selectedOrgId,
        wazuh_host: wazuhHost.trim(),
        wazuh_port: Number(wazuhPort),
        wazuh_api_key: wazuhApiKey.trim()
      });
      addToast({
        type: 'success',
        title: 'Wazuh connected',
        message: 'Successfully updated Wazuh manager settings',
      });
      await loadIntegrationStatus(selectedOrgId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save Wazuh manager connection');
    } finally {
      setBusy(false);
    }
  };

  const handleConfigureSplunk = async () => {
    if (!selectedOrgId || !splunkBaseUrl.trim() || !splunkHecToken.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await configureSplunkHec(selectedOrgId, splunkBaseUrl.trim(), splunkHecToken.trim());
      addToast({
        type: 'success',
        title: 'Splunk HEC configured',
        message: 'Successfully updated Splunk HEC credentials',
      });
      await loadIntegrationStatus(selectedOrgId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to configure Splunk HEC');
    } finally {
      setBusy(false);
    }
  };

  const handleDisconnectSplunk = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    try {
      await removeSplunkConfig(selectedOrgId);
      addToast({
        type: 'info',
        title: 'Splunk disconnected',
        message: 'Splunk HEC credentials removed successfully',
      });
      await loadIntegrationStatus(selectedOrgId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect Splunk');
    } finally {
      setBusy(false);
    }
  };

  const handleMockTelemetry = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const res = await seedMockSplunkFindings(selectedOrgId);
      addToast({
        type: 'success',
        title: 'Telemetry stream seeded',
        message: `Successfully ingested ${res.inserted} telemetry verification events. GHI calculation updated.`,
      });
      setNotice(`Mock telemetry stream sent successfully. ${res.inserted} controls verified in database.`);
      await loadIntegrationStatus(selectedOrgId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed mock telemetry');
    } finally {
      setBusy(false);
    }
  };

  const selectedOrgName = useMemo(() => {
    return organizations.find((o) => o.id === selectedOrgId)?.name || 'Organization';
  }, [organizations, selectedOrgId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#00C853] animate-spin mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-350 font-medium">Resolving data connections...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-50/10 dark:bg-emerald-950/20 border border-emerald-250 dark:border-emerald-800/40 rounded-2xl flex items-center justify-center">
            <PlugZap className="w-5 h-5 text-[#00C853]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Connect Security Data Sources
            </h1>
            <p className="text-slate-500 dark:text-slate-450 text-sm font-semibold">
              Establish continuous SIEM data connections to enable continuous governance.
            </p>
          </div>
        </div>
        <div>
          <Select
            label="Target Organization"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            options={organizations.map((org) => ({ value: org.id, label: org.name }))}
            disabled={busy}
          />
        </div>
      </div>

      {error && (
        <Card className="rounded-2xl border-red-200 bg-red-50/20 dark:bg-red-950/10 dark:border-red-900/40 shadow-sm">
          <CardContent className="py-3.5 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-400 font-bold">{error}</p>
          </CardContent>
        </Card>
      )}

      {notice && (
        <Card className="rounded-2xl border-green-200 bg-green-50/20 dark:bg-green-950/10 dark:border-green-900/40 shadow-sm">
          <CardContent className="py-3.5 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#00C853] shrink-0" />
            <p className="text-sm text-green-700 dark:text-green-400 font-bold">{notice}</p>
          </CardContent>
        </Card>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Wazuh Card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md hover:border-slate-350 dark:hover:border-slate-750 transition-all duration-300">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-500" />
                Wazuh SOC Manager
              </CardTitle>
              <Badge variant={wazuhConnected ? 'success' : 'outline'} className="gap-1.5 rounded-xl px-2.5 py-0.5 font-bold">
                <span className={`inline-block h-2 w-2 rounded-full ${wazuhConnected ? 'bg-[#00C853] animate-pulse' : 'bg-slate-400'}`} />
                {wazuhConnected ? 'Connected' : wazuhConfigured ? 'Offline' : 'Not Configured'}
              </Badge>
            </div>
            <CardDescription className="text-xs font-semibold">
              Connect to Wazuh manager API to sync active agents status & CVEs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            <Input
              label="Manager Host / IP"
              value={wazuhHost}
              onChange={(e) => setWazuhHost(e.target.value)}
              placeholder="e.g. wazuh.internal.company.com"
              disabled={busy || isReadOnly}
            />
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-1">
                <Input
                  label="Port"
                  type="number"
                  value={String(wazuhPort)}
                  onChange={(e) => setWazuhPort(Number(e.target.value) || 55000)}
                  placeholder="55000"
                  disabled={busy || isReadOnly}
                />
              </div>
              <div className="col-span-2">
                <Input
                  label="API Password / Key"
                  type="password"
                  value={wazuhApiKey}
                  onChange={(e) => setWazuhApiKey(e.target.value)}
                  placeholder="••••••••••••"
                  disabled={busy || isReadOnly}
                />
              </div>
            </div>
            {wazuhAgents && (
              <div className="p-3 bg-slate-100/50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 text-xs font-bold text-slate-700 dark:text-slate-300">
                Live Status: {wazuhAgents.active} / {wazuhAgents.total} Agents Active
              </div>
            )}
          </CardContent>
          <CardFooter className="pt-2">
            <Button
              onClick={handleConfigureWazuh}
              disabled={busy || !wazuhHost.trim() || isReadOnly}
              className="w-full bg-[#00C853] hover:bg-[#00C853]/90 text-white rounded-xl font-bold gap-1.5"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Save & Test Connection
            </Button>
          </CardFooter>
        </Card>

        {/* Splunk Card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md hover:border-slate-350 dark:hover:border-slate-750 transition-all duration-300">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-500" />
                Splunk Endpoint HEC
              </CardTitle>
              <Badge variant={splunkConfigured ? 'success' : 'outline'} className="gap-1.5 rounded-xl px-2.5 py-0.5 font-bold">
                <span className={`inline-block h-2 w-2 rounded-full ${splunkConfigured ? 'bg-[#00C853] animate-pulse' : 'bg-slate-400'}`} />
                {splunkConfigured ? 'Active' : 'Not Configured'}
              </Badge>
            </div>
            <CardDescription className="text-xs font-semibold">
              Configure Splunk HTTP Event Collector for real-time control checks.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {splunkConfigured ? (
              <div className="space-y-2 p-3 bg-slate-100/50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 text-xs font-bold text-slate-700 dark:text-slate-300">
                <p>Endpoint URL: <span className="font-mono text-purple-600 dark:text-purple-400">{splunkConfigUrl}</span></p>
                {splunkEvidenceCount !== null && (
                  <p className="mt-1">Verified Controls via Splunk: <span className="text-[#00C853]">{splunkEvidenceCount} Controls</span></p>
                )}
              </div>
            ) : (
              <>
                <Input
                  label="Splunk Base URL"
                  value={splunkBaseUrl}
                  onChange={(e) => setSplunkBaseUrl(e.target.value)}
                  placeholder="https://splunk-hec.company.com:8088"
                  disabled={busy || isReadOnly}
                />
                <Input
                  label="HEC Token"
                  type="password"
                  value={splunkHecToken}
                  onChange={(e) => setSplunkHecToken(e.target.value)}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  disabled={busy || isReadOnly}
                />
              </>
            )}
          </CardContent>
          <CardFooter className="pt-2 gap-2 flex">
            {splunkConfigured ? (
              <Button
                onClick={handleDisconnectSplunk}
                variant="outline"
                disabled={busy || isReadOnly}
                className="w-full text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 border-red-200 dark:border-red-900/40 rounded-xl font-bold"
              >
                Disconnect Splunk
              </Button>
            ) : (
              <Button
                onClick={handleConfigureSplunk}
                disabled={busy || !splunkBaseUrl.trim() || !splunkHecToken.trim() || isReadOnly}
                className="w-full bg-[#00C853] hover:bg-[#00C853]/90 text-white rounded-xl font-bold"
              >
                Enable HEC Ingestion
              </Button>
            )}
          </CardFooter>
        </Card>

        {/* Custom Telemetry Card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md hover:border-slate-350 dark:hover:border-slate-750 transition-all duration-300 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-amber-500" />
              Custom API & Webhook Ingestion
            </CardTitle>
            <CardDescription className="text-xs font-semibold">
              Push continuous telemetry updates directly to ResilAI using webhook signature verification.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2">
                <Webhook className="w-4 h-4 text-slate-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">SIEM Webhook Endpoint</span>
              </div>
              <pre className="p-3 bg-slate-950 border border-slate-800 text-green-400 font-mono text-xs rounded-xl overflow-x-auto select-all">
                {`${window.location.origin}/api/v1/integrations/siem/event`}
              </pre>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold leading-relaxed">
                Add this URL as a webhook target in Splunk, Elastic, or Wazuh. ResilAI validates the payload integrity using standard HMAC signatures.
              </p>
            </div>
            <div className="space-y-2.5">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#00C853]" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">Interactive Simulation</span>
              </div>
              <p className="text-xs text-slate-550 dark:text-slate-400 font-semibold leading-relaxed">
                For staging and investor demos, trigger a simulated flow of live security telemetry signals below.
              </p>
              <Button
                onClick={handleMockTelemetry}
                disabled={busy}
                className="w-full bg-violet-600 hover:bg-violet-750 text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-sm"
              >
                <Play className="w-4 h-4 shrink-0 fill-current" />
                Trigger Telemetry Event Flow
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
