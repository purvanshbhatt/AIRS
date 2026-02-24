import { Code, ExternalLink, Terminal, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { getApiBaseUrl } from '../../api';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-3 p-1.5 rounded-md bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
    </button>
  );
}

const ENDPOINTS = [
  { method: 'GET', path: '/health', description: 'Backend health check', auth: false },
  { method: 'GET', path: '/health/system', description: 'Runtime status and environment', auth: false },
  { method: 'GET', path: '/api/scoring/rubric', description: 'Assessment questions and scoring rubric', auth: true },
  { method: 'POST', path: '/api/assessments', description: 'Create assessment', auth: true },
  { method: 'POST', path: '/api/assessments/{assessment_id}/answers', description: 'Submit assessment answers', auth: true },
  { method: 'POST', path: '/api/assessments/{assessment_id}/score', description: 'Compute and persist score', auth: true },
  { method: 'GET', path: '/api/assessments/{assessment_id}/summary', description: 'Full results payload for UI', auth: true },
  { method: 'GET', path: '/api/assessments/{assessment_id}/executive-summary', description: 'Download 1-page executive PDF', auth: true },
  { method: 'GET', path: '/api/assessments/{assessment_id}/export', description: 'Export findings for SIEM JSON ingestion', auth: true },
  { method: 'POST', path: '/api/orgs/{org_id}/api-keys', description: 'Generate external API key', auth: true },
  { method: 'POST', path: '/api/orgs/{org_id}/webhooks', description: 'Create outbound webhook', auth: true },
  { method: 'POST', path: '/api/integrations/mock/splunk-seed', description: 'Seed synthetic Splunk findings', auth: true },
  { method: 'GET', path: '/api/integrations/external-findings?source=splunk&limit=50', description: 'List external findings', auth: true },
];

export default function DocsApi() {
  const apiBaseUrl = getApiBaseUrl();
  const openApiUrl = `${apiBaseUrl}/docs`;

  return (
    <div className="space-y-10">
      <div>
        <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-3">
          <Code className="w-5 h-5" />
          <span className="text-sm font-medium">API Reference</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">ResilAI API</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl">
          Programmatic access for assessments, scoring, executive reporting, and integration hooks.
        </p>
      </div>

      <section className="p-6 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-xl border border-primary-200 dark:border-primary-800">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">Interactive API Docs</h2>
            <p className="text-gray-600 dark:text-gray-400">Swagger UI for live endpoint exploration.</p>
          </div>
          <a
            href={openApiUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Open Swagger
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-3">Base URL</h2>
        <div className="relative">
          <pre className="p-4 bg-gray-900 dark:bg-gray-950 text-gray-100 rounded-lg overflow-x-auto">
            <code>{apiBaseUrl}</code>
          </pre>
          <CopyButton text={apiBaseUrl} />
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-3">Authentication</h2>
        <div className="space-y-4">
          <div className="p-5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <p className="text-gray-600 dark:text-gray-400 mb-3">
              User-scoped routes require Firebase ID tokens via bearer auth.
            </p>
            <div className="relative">
              <pre className="p-4 bg-gray-900 dark:bg-gray-950 text-gray-100 rounded-lg overflow-x-auto text-sm">
                <code>{`Authorization: Bearer <firebase_id_token>`}</code>
              </pre>
            </div>
          </div>
          <div className="p-5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <p className="text-gray-600 dark:text-gray-400 mb-3">
              External pull integrations can use API key auth on supported endpoints.
            </p>
            <div className="relative">
              <pre className="p-4 bg-gray-900 dark:bg-gray-950 text-gray-100 rounded-lg overflow-x-auto text-sm">
                <code>{`X-AIRS-API-Key: airs_live_<key_value>`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Core Endpoints</h2>
        <div className="space-y-3">
          {ENDPOINTS.map((endpoint) => (
            <div
              key={`${endpoint.method}-${endpoint.path}`}
              className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <span
                className={`w-fit px-2 py-1 text-xs font-mono font-bold rounded ${
                  endpoint.method === 'GET'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                }`}
              >
                {endpoint.method}
              </span>
              <code className="font-mono text-sm text-gray-700 dark:text-gray-300 flex-1">{endpoint.path}</code>
              <span className="text-sm text-gray-500 dark:text-gray-400 flex-[1.4]">{endpoint.description}</span>
              {endpoint.auth && (
                <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded">
                  Auth
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
          <Terminal className="w-6 h-6 text-primary-600" />
          Example Request
        </h2>
        <div className="relative">
          <pre className="p-4 bg-gray-900 dark:bg-gray-950 text-gray-100 rounded-lg overflow-x-auto text-sm">
            <code>{`curl -X GET \\
  ${apiBaseUrl}/api/assessments/{assessment_id}/summary \\
  -H "Authorization: Bearer <firebase_id_token>"`}</code>
          </pre>
          <CopyButton
            text={`curl -X GET ${apiBaseUrl}/api/assessments/{assessment_id}/summary -H "Authorization: Bearer <firebase_id_token>"`}
          />
        </div>
      </section>
    </div>
  );
}

