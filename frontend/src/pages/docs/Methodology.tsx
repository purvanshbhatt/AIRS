import { BarChart3, Scale, Target, TrendingUp, Info } from 'lucide-react';

export default function DocsMethodology() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-4">
                    <BarChart3 className="w-5 h-5" />
                    <span className="text-sm font-medium">Methodology</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Scoring Methodology
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl">
                    Learn how ResilAI calculates readiness scores across five security domains
                    and determines organizational maturity levels.
                </p>
            </div>

            {/* Domains */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <Target className="w-6 h-6 text-primary-600" />
                    Assessment Domains
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                    ResilAI evaluates your security posture across five critical domains, each with
                    a specific weight reflecting its importance in incident response readiness.
                </p>

                <div className="space-y-4">
                    {[
                        {
                            name: 'Telemetry & Logging',
                            weight: 25,
                            color: 'bg-blue-500',
                            description: 'Measures log collection coverage, retention periods, and centralization. Essential for forensics and detection.'
                        },
                        {
                            name: 'Detection Coverage',
                            weight: 20,
                            color: 'bg-green-500',
                            description: 'Evaluates EDR deployment, network monitoring, detection rule freshness, and alert triage speed.'
                        },
                        {
                            name: 'Identity Visibility',
                            weight: 20,
                            color: 'bg-purple-500',
                            description: 'Assesses MFA enforcement, privileged account management, PAM deployment, and anomaly monitoring.'
                        },
                        {
                            name: 'IR Playbooks & Process',
                            weight: 15,
                            color: 'bg-orange-500',
                            description: 'Reviews incident response documentation, team structure, communication plans, and exercise frequency.'
                        },
                        {
                            name: 'Backup/Recovery & Resilience',
                            weight: 20,
                            color: 'bg-red-500',
                            description: 'Examines backup practices, immutability, recovery testing, RTO targets, and disaster recovery planning.'
                        },
                    ].map((domain) => (
                        <div
                            key={domain.name}
                            className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                        >
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-gray-900 dark:text-gray-100">{domain.name}</h3>
                                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{domain.weight}% weight</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-3">
                                <div className={`${domain.color} h-2 rounded-full`} style={{ width: `${domain.weight}%` }} />
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{domain.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* How Domain Weights Are Determined */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <Info className="w-6 h-6 text-primary-600" />
                    How Domain Weights Are Determined
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Domain weights are not arbitrary — they are derived from four evidence-based factors
                    that reflect real-world incident impact and regulatory expectations.
                </p>

                <div className="grid sm:grid-cols-2 gap-4 mb-6">
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                        <h4 className="font-medium text-red-800 dark:text-red-300 mb-2">MITRE ATT&CK Prevalence</h4>
                        <p className="text-sm text-red-700 dark:text-red-400">
                            Domains covering the most frequently observed attacker techniques (per MITRE
                            data and threat intelligence) receive higher weight. Detection and telemetry
                            cover the widest range of T-codes.
                        </p>
                    </div>
                    <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                        <h4 className="font-medium text-emerald-800 dark:text-emerald-300 mb-2">NIST CSF Function Criticality</h4>
                        <p className="text-sm text-emerald-700 dark:text-emerald-400">
                            Each domain aligns to a NIST CSF 2.0 lifecycle function (Detect, Protect, Respond,
                            Recover). Functions that span more CSF categories receive proportionally greater
                            weight to ensure lifecycle coverage.
                        </p>
                    </div>
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2">Breach Root-Cause Analysis</h4>
                        <p className="text-sm text-blue-700 dark:text-blue-400">
                            Weights reflect confirmed breach enablers from CISA advisories, FBI IC3 reports,
                            and the Verizon DBIR. Telemetry and detection gaps are implicated in a majority
                            of successful ransomware incidents.
                        </p>
                    </div>
                    <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                        <h4 className="font-medium text-amber-800 dark:text-amber-300 mb-2">Regulatory Exposure</h4>
                        <p className="text-sm text-amber-700 dark:text-amber-400">
                            Domains with direct compliance implications (identity access controls, audit
                            logging, incident response documentation) are weighted to reflect obligations
                            under SEC, HIPAA, PCI-DSS, and NIS2 frameworks.
                        </p>
                    </div>
                </div>

                {/* Weight Distribution Visual */}
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Weight Distribution:</h4>
                    <div className="space-y-3">
                        {[
                            { name: 'Telemetry & Logging', weight: 25, function: 'DE', color: 'bg-blue-500', reason: 'Highest ATT&CK coverage; forensic prerequisite for all downstream detection' },
                            { name: 'Detection Coverage', weight: 20, function: 'DE', color: 'bg-green-500', reason: 'Primary defense against active intrusion; EDR is the #1 ransomware preventive' },
                            { name: 'Identity Visibility', weight: 20, function: 'PR', color: 'bg-purple-500', reason: 'Credential compromise is the leading initial access vector (DBIR, IC3)' },
                            { name: 'Backup/Recovery', weight: 20, function: 'RC', color: 'bg-red-500', reason: 'Operational resilience; ransomware recovery without payment depends on this' },
                            { name: 'IR Playbooks', weight: 15, function: 'RS', color: 'bg-orange-500', reason: 'Response coordination; lower weight reflects dependence on other controls' },
                        ].map((d) => (
                            <div key={d.name} className="flex items-center gap-3">
                                <div className="w-32 text-sm font-medium text-gray-700 dark:text-gray-300 truncate" title={d.name}>{d.name}</div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <div className={`h-full ${d.color} rounded-full`} style={{ width: `${d.weight}%` }} />
                                        </div>
                                        <span className="text-xs font-mono font-bold text-gray-500 dark:text-gray-400 w-8">{d.weight}%</span>
                                        <span className="text-[10px] font-mono text-gray-400 dark:text-gray-500 w-6">{d.function}</span>
                                    </div>
                                    <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{d.reason}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                        Weights sum to 100%. They are applied multiplicatively to each domain's 0–5 raw score
                        to produce the overall 0–100 Risk Posture index. Weights are reviewed quarterly against
                        updated threat intelligence.
                    </p>
                </div>
            </section>

            {/* Scoring Formula */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <Scale className="w-6 h-6 text-primary-600" />
                    Scoring Formula
                </h2>

                <div className="p-6 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-4">
                    <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Domain Score (0-5 scale)</h3>
                        <code className="block p-3 bg-gray-900 dark:bg-gray-950 text-green-400 rounded-lg text-sm">
                            domain_score = (points_earned / max_points) × 5
                        </code>
                    </div>

                    <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Overall Score (0-100 scale)</h3>
                        <code className="block p-3 bg-gray-900 dark:bg-gray-950 text-green-400 rounded-lg text-sm">
                            overall_score = Σ (domain_score / 5) × domain_weight
                        </code>
                    </div>

                    <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Question Types:</h4>
                        <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                            <li><strong>Boolean:</strong> Yes = 1 point, No = 0 points</li>
                            <li><strong>Percentage:</strong> Threshold-based scoring (e.g., 95%+ = 1.0, 75%+ = 0.75)</li>
                            <li><strong>Numeric:</strong> Threshold-based scoring with direction (higher or lower is better)</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Maturity Levels */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <TrendingUp className="w-6 h-6 text-primary-600" />
                    Maturity Levels
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Based on your overall score, ResilAI assigns a maturity level that describes
                    your organization's current state of incident response readiness.
                </p>

                <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Level</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Name</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Score Range</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Description</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
                            {[
                                { level: 1, name: 'Initial', range: '0-20', description: 'Ad-hoc, reactive security posture', color: 'text-red-600' },
                                { level: 2, name: 'Developing', range: '21-40', description: 'Basic controls in place, gaps exist', color: 'text-orange-600' },
                                { level: 3, name: 'Defined', range: '41-60', description: 'Documented processes, consistent execution', color: 'text-yellow-600' },
                                { level: 4, name: 'Managed', range: '61-80', description: 'Measured and controlled, proactive approach', color: 'text-green-600' },
                                { level: 5, name: 'Optimized', range: '81-100', description: 'Continuous improvement, industry-leading', color: 'text-primary-600' },
                            ].map((level) => (
                                <tr key={level.level}>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 font-semibold ${level.color}`}>
                                            {level.level}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{level.name}</td>
                                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{level.range}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{level.description}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}

