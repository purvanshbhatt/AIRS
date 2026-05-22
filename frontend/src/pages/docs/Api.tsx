import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Code,
  ExternalLink,
  Terminal,
  Copy,
  Check,
  Menu,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Layers,
  FileCheck,
  Radio,
  FileText,
  Key,
} from 'lucide-react';
import { getApiBaseUrl } from '../../api';

interface Endpoint {
  method: 'GET' | 'POST';
  path: string;
  description: string;
  auth: boolean;
}

const GROUPS = [
  {
    id: 'intro',
    title: 'Authentication & Basics',
    icon: Key,
    description: 'Learn how to authenticate requests using bearer tokens or api keys.',
  },
  {
    id: 'assessments',
    title: 'Assessments API',
    icon: FileCheck,
    description: 'Initialize assessments, submit responses, and fetch calculated scores.',
  },
  {
    id: 'remediation',
    title: 'Remediation API',
    icon: Layers,
    description: 'Pull posture highlights, list action items, and download PDF summaries.',
  },
  {
    id: 'siem',
    title: 'SIEM Integration',
    icon: Radio,
    description: 'Sync system alerts and feed logs into wazuh or splunk connectors.',
  },
];

const ENDPOINTS_BY_GROUP: Record<string, Endpoint[]> = {
  intro: [
    { method: 'GET', path: '/health', description: 'Backend health check', auth: false },
    { method: 'GET', path: '/health/system', description: 'Runtime status and environment', auth: false },
  ],
  assessments: [
    { method: 'GET', path: '/api/scoring/rubric', description: 'Assessment questions and scoring rubric', auth: true },
    { method: 'POST', path: '/api/assessments', description: 'Create new assessment', auth: true },
    { method: 'POST', path: '/api/assessments/{assessment_id}/answers', description: 'Submit assessment answers', auth: true },
    { method: 'POST', path: '/api/assessments/{assessment_id}/score', description: 'Compute and persist score', auth: true },
    { method: 'GET', path: '/api/assessments/{assessment_id}/summary', description: 'Full results payload for UI', auth: true },
  ],
  remediation: [
    { method: 'GET', path: '/api/assessments/{assessment_id}/executive-summary', description: 'Download executive PDF summary', auth: true },
    { method: 'GET', path: '/api/assessments/{assessment_id}/export', description: 'Export findings for SIEM JSON ingestion', auth: true },
  ],
  siem: [
    { method: 'POST', path: '/api/orgs/{org_id}/api-keys', description: 'Generate external API key', auth: true },
    { method: 'POST', path: '/api/orgs/{org_id}/webhooks', description: 'Create outbound webhook', auth: true },
    { method: 'POST', path: '/api/integrations/mock/splunk-seed', description: 'Seed synthetic Splunk findings', auth: true },
    { method: 'GET', path: '/api/integrations/external-findings?source=splunk&limit=50', description: 'List external findings', auth: true },
  ],
};

function SnippetWidget({ path, method }: { path: string; method: string }) {
  const [lang, setLang] = useState<'curl' | 'python' | 'js'>('curl');
  const [copied, setCopied] = useState(false);
  const apiBaseUrl = getApiBaseUrl();

  const curlCode = `curl -X ${method} "${apiBaseUrl}${path}" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer resil_live_83fa9b12a819cd6f"`;

  const pythonCode = `import requests

url = "${apiBaseUrl}${path}"
headers = {
    "Accept": "application/json",
    "Authorization": "Bearer resil_live_83fa9b12a819cd6f"
}

response = requests.${method.toLowerCase()}(url, headers=headers)
print(response.json())`;

  const jsCode = `fetch("${apiBaseUrl}${path}", {
  method: "${method}",
  headers: {
    "Accept": "application/json",
    "Authorization": "Bearer resil_live_83fa9b12a819cd6f"
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));`;

  const getCode = () => {
    if (lang === 'python') return pythonCode;
    if (lang === 'js') return jsCode;
    return curlCode;
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(getCode());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative rounded-2xl bg-slate-950 border border-slate-800 dark:border-slate-900 overflow-hidden font-mono text-left shadow-lg">
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/60 border-b border-slate-900">
        <div className="flex gap-1.5">
          <button
            onClick={() => setLang('curl')}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
              lang === 'curl' ? 'bg-slate-850 text-blue-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            cURL
          </button>
          <button
            onClick={() => setLang('python')}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
              lang === 'python' ? 'bg-slate-850 text-blue-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Python
          </button>
          <button
            onClick={() => setLang('js')}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
              lang === 'js' ? 'bg-slate-850 text-blue-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            JS Fetch
          </button>
        </div>
        <button
          onClick={handleCopy}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Copy code"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-[11px] text-slate-350 max-h-72">
        <pre className="whitespace-pre">{getCode()}</pre>
      </div>
    </div>
  );
}

export default function DocsApi() {
  const [collapsed, setCollapsed] = useState(false);
  const [activeGroup, setActiveGroup] = useState('intro');
  const apiBaseUrl = getApiBaseUrl();
  const openApiUrl = `${apiBaseUrl}/docs`;

  return (
    <div className="flex flex-col lg:flex-row gap-8 min-h-[calc(100vh-140px)]">
      {/* Sidebar Nav */}
      <motion.aside
        animate={{ width: collapsed ? 64 : 260 }}
        transition={{ type: 'spring', damping: 22, stiffness: 200 }}
        className="shrink-0 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-3 flex flex-col relative"
      >
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-6 w-6 h-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full flex items-center justify-center text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 shadow-sm z-10"
        >
          {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>

        <div className="p-2 mb-4 flex items-center gap-2 overflow-hidden select-none">
          <Code className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0" />
          {!collapsed && (
            <span className="font-bold text-sm tracking-tight text-slate-950 dark:text-slate-50">
              API Reference
            </span>
          )}
        </div>

        <nav className="space-y-1.5 flex-1">
          {GROUPS.map((g) => {
            const Icon = g.icon;
            const active = activeGroup === g.id;
            return (
              <button
                key={g.id}
                onClick={() => setActiveGroup(g.id)}
                className={`w-full flex items-center gap-3 p-3 rounded-2xl text-left transition-all ${
                  active
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4.5 h-4.5 shrink-0" />
                {!collapsed && (
                  <span className="text-xs font-semibold truncate leading-none">
                    {g.title}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </motion.aside>

      {/* Main pane */}
      <div className="flex-1 space-y-10 text-left">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-950 dark:text-slate-50 mb-2">ResilAI REST API</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl leading-relaxed">
            Integrate security scoring, audit triggers, and continuous compliance alerts into your pipeline.
          </p>
        </div>

        {/* Interactive Swagger Link Panel */}
        <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 rounded-3xl border border-blue-100 dark:border-blue-900/40 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50 mb-1">OpenAPI Interactive Swagger</h2>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Use your API Keys to test actual endpoints live from your browser context.
            </p>
          </div>
          <a
            href={openApiUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4.5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-2xl shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Launch Swagger
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Active Group Details */}
        {activeGroup === 'intro' && (
          <section className="space-y-6">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Base URL &amp; Authorization</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Base endpoint structure and header signatures.</p>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-350 mb-2">Base Endpoint (VITE_API_BASE_URL)</p>
                <div className="relative">
                  <pre className="p-4 bg-slate-950 border border-slate-850 rounded-2xl text-xs font-mono text-slate-200 overflow-x-auto">
                    <code>{apiBaseUrl}</code>
                  </pre>
                  <button
                    onClick={async () => {
                      await navigator.clipboard.writeText(apiBaseUrl);
                    }}
                    className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 text-slate-400 hover:text-slate-250 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6 pt-2">
                <div className="p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <Key className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-50">Firebase ID Token</span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-450 leading-relaxed mb-4">
                    Required for user-scoped dashboard routes. Exchanged from client login flow.
                  </p>
                  <pre className="p-3.5 bg-slate-950 rounded-xl text-[10px] font-mono text-slate-300 overflow-x-auto">
                    <code>{`Authorization: Bearer <token>`}</code>
                  </pre>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-50">Headless API Key</span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-450 leading-relaxed mb-4">
                    Generated under Settings &gt; Integrations. Used for outbound telemetry scripts.
                  </p>
                  <pre className="p-3.5 bg-slate-950 rounded-xl text-[10px] font-mono text-slate-300 overflow-x-auto">
                    <code>{`X-AIRS-API-Key: airs_live_<key>`}</code>
                  </pre>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Dynamic Categorized Endpoint List */}
        <section className="space-y-6">
          {activeGroup !== 'intro' && (
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                {GROUPS.find((g) => g.id === activeGroup)?.title}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {GROUPS.find((g) => g.id === activeGroup)?.description}
              </p>
            </div>
          )}

          <div className="space-y-6">
            {(ENDPOINTS_BY_GROUP[activeGroup] || []).map((endpoint) => (
              <div
                key={`${endpoint.method}-${endpoint.path}`}
                className="p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200/85 dark:border-slate-800/85 rounded-2xl space-y-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`px-2.5 py-1 text-[10px] font-mono font-bold rounded-lg ${
                        endpoint.method === 'GET'
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-350'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-350'
                      }`}
                    >
                      {endpoint.method}
                    </span>
                    <code className="font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
                      {endpoint.path}
                    </code>
                  </div>
                  <div className="flex items-center gap-2">
                    {endpoint.auth && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-50 dark:bg-amber-950/30 border border-amber-250/30 dark:border-amber-900/30 text-amber-700 dark:text-amber-400 rounded-md">
                        Auth Token Required
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-650 dark:text-slate-350">{endpoint.description}</p>

                {/* Tabbed Interactive Code Widget */}
                <div className="space-y-2">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Example Integration Snippet</p>
                  <SnippetWidget path={endpoint.path} method={endpoint.method} />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
