import React from 'react';
import { Shield, ExternalLink, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';

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

            {/* NIST CSF 2.0 */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-teal-100 dark:bg-teal-900/30 rounded-lg">
                        <Shield className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        NIST Cybersecurity Framework 2.0
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                        Every assessment question maps to one of the six NIST CSF 2.0 lifecycle functions,
                        providing end-to-end coverage across the cybersecurity risk management lifecycle.
                        This ensures findings address governance, prevention, detection, and recovery equally.
                    </p>

                    {/* Lifecycle Diagram */}
                    <div className="mb-6">
                        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">CSF 2.0 Lifecycle Functions:</h3>
                        <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
                            {[
                                { code: 'GV', name: 'Govern', color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600', description: 'Establish and monitor cybersecurity risk management strategy, expectations, and policy' },
                                { code: 'ID', name: 'Identify', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700', description: 'Understand organizational context, assets, and risk to prioritize efforts' },
                                { code: 'PR', name: 'Protect', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700', description: 'Implement safeguards to ensure delivery of critical services' },
                                { code: 'DE', name: 'Detect', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700', description: 'Identify the occurrence of cybersecurity events in a timely manner' },
                                { code: 'RS', name: 'Respond', color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-700', description: 'Take action regarding a detected cybersecurity incident' },
                                { code: 'RC', name: 'Recover', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-700', description: 'Restore capabilities or services impaired by a cybersecurity incident' },
                            ].map((func, index) => (
                                <React.Fragment key={func.code}>
                                    <div className={`px-4 py-3 rounded-lg border ${func.color} text-center min-w-[100px]`}>
                                        <div className="text-lg font-bold font-mono">{func.code}</div>
                                        <div className="text-sm font-medium">{func.name}</div>
                                    </div>
                                    {index < 5 && (
                                        <RefreshCw className="w-4 h-4 text-gray-300 dark:text-gray-600 hidden sm:block" />
                                    )}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>

                    {/* Function Details */}
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                        {[
                            { code: 'GV', name: 'Govern', desc: 'Establish and monitor cybersecurity risk management strategy, expectations, and policy.', color: 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/20' },
                            { code: 'ID', name: 'Identify', desc: 'Understand organizational context, assets, and risk to prioritize cybersecurity efforts.', color: 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20' },
                            { code: 'PR', name: 'Protect', desc: 'Implement safeguards such as MFA, PAM, and access controls to ensure delivery of services.', color: 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20' },
                            { code: 'DE', name: 'Detect', desc: 'Identify cybersecurity events through EDR, log monitoring, and alert triage processes.', color: 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20' },
                            { code: 'RS', name: 'Respond', desc: 'Take action on detected incidents through IR playbooks, communication plans, and containment.', color: 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20' },
                            { code: 'RC', name: 'Recover', desc: 'Restore impaired capabilities via backup recovery, RTO targets, and DR planning.', color: 'border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20' },
                        ].map((func) => (
                            <div key={func.code} className={`p-3 rounded-lg border ${func.color}`}>
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-mono font-bold">{func.code}</span>
                                    <span className="font-medium text-sm text-gray-900 dark:text-gray-100">{func.name}</span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">{func.desc}</p>
                            </div>
                        ))}
                    </div>

                    {/* Domain Mapping */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 mb-6">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                            How Assessment Domains Map to NIST CSF 2.0:
                        </h4>
                        <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-amber-700 dark:text-amber-300">DE</span>
                                <span>Telemetry &amp; Logging — Detect: Continuous Monitoring (DE.CM)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-amber-700 dark:text-amber-300">DE</span>
                                <span>Detection Coverage — Detect: Adverse Event Analysis (DE.AE)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-green-700 dark:text-green-300">PR</span>
                                <span>Identity Visibility — Protect: Identity Management &amp; Access Control (PR.AA)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-orange-700 dark:text-orange-300">RS</span>
                                <span>IR Playbooks &amp; Process — Respond: Incident Management (RS.MA)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-purple-700 dark:text-purple-300">RC</span>
                                <span>Backup/Recovery &amp; Resilience — Recover: Incident Recovery Plan Execution (RC.RP)</span>
                            </div>
                        </div>
                    </div>

                    <a
                        href="https://www.nist.gov/cyberframework"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline"
                    >
                        Learn more about NIST CSF 2.0
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

