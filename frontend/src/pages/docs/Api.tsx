import { Code, ExternalLink, Terminal, Copy, Check } from 'lucide-react';
import { useState } from 'react';

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
            className="absolute top-3 right-3 p-1.5 rounded-md bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-gray-300 transition-colors"
            title="Copy to clipboard"
        >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
        </button>
    );
}

export default function DocsApi() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 mb-4">
                    <Code className="w-5 h-5" />
                    <span className="text-sm font-medium">API Reference</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    ResilAI API
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl">
                    The ResilAI REST API allows you to programmatically run assessments,
                    retrieve scores, and generate reports.
                </p>
            </div>

            {/* OpenAPI Link */}
            <section className="p-6 bg-gradient-to-r from-primary-50 to-primary-100/20 rounded-xl border border-primary-200">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            Interactive API Documentation
                        </h2>
                        <p className="text-gray-600">
                            Explore the full API specification with Swagger UI
                        </p>
                    </div>
                    <a
                        href="https://airs-api-227825933697.us-central1.run.app/docs"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                    >
                        Open API Docs
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* Base URL */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                    Base URL
                </h2>
                <div className="relative">
                    <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto">
                        <code>https://airs-api-227825933697.us-central1.run.app</code>
                    </pre>
                    <CopyButton text="https://airs-api-227825933697.us-central1.run.app" />
                </div>
            </section>

            {/* Authentication */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                    Authentication
                </h2>
                <div className="p-6 bg-white rounded-xl border border-gray-200">
                    <p className="text-gray-600 mb-4">
                        API requests require a Bearer token obtained from Firebase Authentication.
                    </p>
                    <div className="relative">
                        <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm">
                            <code>{`Authorization: Bearer <firebase_id_token>`}</code>
                        </pre>
                    </div>
                </div>
            </section>

            {/* Key Endpoints */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                    Key Endpoints
                </h2>

                <div className="space-y-4">
                    {[
                        {
                            method: 'GET',
                            path: '/health',
                            description: 'Check API health status',
                            auth: false,
                        },
                        {
                            method: 'GET',
                            path: '/api/v1/rubric',
                            description: 'Get the complete scoring rubric with domains and questions',
                            auth: false,
                        },
                        {
                            method: 'POST',
                            path: '/api/v1/scores/calculate',
                            description: 'Calculate scores from assessment answers',
                            auth: false,
                        },
                        {
                            method: 'POST',
                            path: '/api/v1/organizations',
                            description: 'Create a new organization',
                            auth: true,
                        },
                        {
                            method: 'POST',
                            path: '/api/v1/assessments',
                            description: 'Create and store an assessment',
                            auth: true,
                        },
                        {
                            method: 'GET',
                            path: '/api/v1/assessments/{id}',
                            description: 'Retrieve an assessment by ID',
                            auth: true,
                        },
                        {
                            method: 'POST',
                            path: '/api/v1/reports/generate',
                            description: 'Generate PDF report with AI narrative',
                            auth: true,
                        },
                    ].map((endpoint) => (
                        <div
                            key={endpoint.path}
                            className="flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-200"
                        >
                            <span
                                className={`px-2 py-1 text-xs font-mono font-bold rounded ${endpoint.method === 'GET'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-blue-100 text-blue-700'
                                    }`}
                            >
                                {endpoint.method}
                            </span>
                            <code className="flex-1 text-sm text-gray-700 font-mono">
                                {endpoint.path}
                            </code>
                            <span className="text-sm text-gray-500 hidden md:block">
                                {endpoint.description}
                            </span>
                            {endpoint.auth && (
                                <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                                    Auth
                                </span>
                            )}
                        </div>
                    ))}
                </div>
            </section>

            {/* Example: Calculate Scores */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Terminal className="w-6 h-6 text-primary-600" />
                    Example: Calculate Scores
                </h2>

                <div className="space-y-4">
                    <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Request (cURL)</h3>
                        <div className="relative">
                            <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm">
                                <code>{`curl -X POST \\
  https://airs-api-227825933697.us-central1.run.app/api/v1/scores/calculate \\
  -H "Content-Type: application/json" \\
  -d '{
    "answers": {
      "tl_01": true,
      "tl_02": true,
      "tl_03": false,
      "tl_04": true,
      "tl_05": 90,
      "tl_06": true,
      "dc_01": 85,
      "dc_02": true
    }
  }'`}</code>
                            </pre>
                            <CopyButton text={`curl -X POST https://airs-api-227825933697.us-central1.run.app/api/v1/scores/calculate -H "Content-Type: application/json" -d '{"answers":{"tl_01":true,"tl_02":true,"tl_03":false,"tl_04":true,"tl_05":90,"tl_06":true}}'`} />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Response</h3>
                        <div className="relative">
                            <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm">
                                <code>{`{
  "overall_score": 67.5,
  "max_score": 100,
  "maturity_level": 4,
  "maturity_name": "Managed",
  "maturity_description": "Measured and controlled, proactive approach",
  "domains": [
    {
      "domain_id": "telemetry_logging",
      "domain_name": "Telemetry & Logging",
      "weight": 25,
      "score": 4.17,
      "max_score": 5
    }
  ]
}`}</code>
                            </pre>
                        </div>
                    </div>
                </div>
            </section>

            {/* JavaScript Example */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                    JavaScript Example
                </h2>
                <div className="relative">
                    <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm">
                        <code>{`const response = await fetch(
  'https://airs-api-227825933697.us-central1.run.app/api/v1/scores/calculate',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answers: {
        tl_01: true,
        tl_02: true,
        tl_03: true,
        tl_04: true,
        tl_05: 365,
        tl_06: true,
        // ... more answers
      }
    })
  }
);

const result = await response.json();
console.log(\`Your ResilAI score: \${result.overall_score}\`);`}</code>
                    </pre>
                    <CopyButton text={`const response = await fetch('https://airs-api-227825933697.us-central1.run.app/api/v1/scores/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers: { tl_01: true, tl_02: true } }) });`} />
                </div>
            </section>
        </div>
    );
}


