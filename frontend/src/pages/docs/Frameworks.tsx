import { Shield, ExternalLink, AlertTriangle, CheckCircle } from 'lucide-react';

export default function DocsFrameworks() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-4">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-medium">Frameworks</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Security Framework Mappings
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl">
                    ResilAI findings automatically map to industry-standard security frameworks,
                    enabling compliance alignment and standardized remediation.
                </p>
            </div>

            {/* MITRE ATT&CK */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                        <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        MITRE ATT&CK
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Findings map to specific ATT&CK techniques that adversaries may exploit when
                        security controls are missing. This helps security teams understand the real-world
                        attack behaviors enabled by identified gaps.
                    </p>

                    <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Mapped Tactics:</h3>
                    <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-2 mb-6">
                        {[
                            'Credential Access', 'Persistence', 'Privilege Escalation',
                            'Defense Evasion', 'Discovery', 'Lateral Movement',
                            'Collection', 'Command and Control', 'Exfiltration',
                            'Impact', 'Initial Access', 'Execution'
                        ].map((tactic) => (
                            <div key={tactic} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                {tactic}
                            </div>
                        ))}
                    </div>

                    <a
                        href="https://attack.mitre.org/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline"
                    >
                        Learn more about MITRE ATT&CK
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* CIS Controls */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                        <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        CIS Controls v8
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Findings map to specific CIS Controls, with Implementation Group (IG) classification
                        to help prioritize based on organizational maturity level.
                    </p>

                    <div className="space-y-4 mb-6">
                        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                            <h4 className="font-medium text-green-800 dark:text-green-300 mb-1">IG1 - Basic Cyber Hygiene</h4>
                            <p className="text-sm text-green-700 dark:text-green-400">Essential controls for all organizations. Minimum baseline for security.</p>
                        </div>
                        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                            <h4 className="font-medium text-yellow-800 dark:text-yellow-300 mb-1">IG2 - Enhanced Controls</h4>
                            <p className="text-sm text-yellow-700 dark:text-yellow-400">For organizations handling sensitive data. Builds on IG1.</p>
                        </div>
                        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                            <h4 className="font-medium text-red-800 dark:text-red-300 mb-1">IG3 - Advanced Controls</h4>
                            <p className="text-sm text-red-700 dark:text-red-400">For high-value targets facing sophisticated adversaries.</p>
                        </div>
                    </div>

                    <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Key Control Areas:</h3>
                    <ul className="grid sm:grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400">
                        {[
                            'Control 5: Account Management',
                            'Control 6: Access Control Management',
                            'Control 8: Audit Log Management',
                            'Control 10: Malware Defenses',
                            'Control 11: Data Recovery',
                            'Control 13: Network Monitoring',
                            'Control 17: Incident Response',
                        ].map((control) => (
                            <li key={control} className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-blue-500" />
                                {control}
                            </li>
                        ))}
                    </ul>

                    <a
                        href="https://www.cisecurity.org/controls"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 mt-6 text-primary-600 dark:text-primary-400 hover:underline"
                    >
                        Learn more about CIS Controls
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* OWASP */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                        <Shield className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        OWASP Top 10
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Authentication and access control findings map to OWASP Top 10 categories,
                        providing context for web application and identity security risks.
                    </p>

                    <div className="grid sm:grid-cols-2 gap-4 mb-6">
                        {[
                            { id: 'A01:2021', name: 'Broken Access Control', relevant: true },
                            { id: 'A02:2021', name: 'Cryptographic Failures', relevant: false },
                            { id: 'A07:2021', name: 'Identification and Authentication Failures', relevant: true },
                            { id: 'A09:2021', name: 'Security Logging and Monitoring Failures', relevant: true },
                        ].map((item) => (
                            <div
                                key={item.id}
                                className={`p-3 rounded-lg border ${item.relevant
                                        ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800'
                                        : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-mono text-purple-600 dark:text-purple-400">{item.id}</span>
                                    {item.relevant && (
                                        <span className="text-xs px-1.5 py-0.5 bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded">
                                            Mapped
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-gray-700 dark:text-gray-300">{item.name}</p>
                            </div>
                        ))}
                    </div>

                    <a
                        href="https://owasp.org/Top10/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline"
                    >
                        Learn more about OWASP Top 10
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* How It Works */}
            <section className="p-6 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    How Framework Mapping Works
                </h2>
                <ol className="space-y-3 text-gray-600 dark:text-gray-400">
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm">1</span>
                        <span>Each assessment question is linked to potential security gaps (finding rules)</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm">2</span>
                        <span>Finding rules map to specific framework references (MITRE techniques, CIS controls, OWASP categories)</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm">3</span>
                        <span>Your report includes framework references for each identified gap</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm">4</span>
                        <span>Use this information for compliance reporting and prioritized remediation</span>
                    </li>
                </ol>
            </section>
        </div>
    );
}

