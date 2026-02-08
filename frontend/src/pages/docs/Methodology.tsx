import { BarChart3, Scale, Target, TrendingUp } from 'lucide-react';

export default function DocsMethodology() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 mb-4">
                    <BarChart3 className="w-5 h-5" />
                    <span className="text-sm font-medium">Methodology</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    Scoring Methodology
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl">
                    Learn how AIRS calculates readiness scores across five security domains
                    and determines organizational maturity levels.
                </p>
            </div>

            {/* Domains */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <Target className="w-6 h-6 text-primary-600" />
                    Assessment Domains
                </h2>
                <p className="text-gray-600 mb-6">
                    AIRS evaluates your security posture across five critical domains, each with
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
                            className="p-4 bg-white rounded-lg border border-gray-200"
                        >
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-gray-900">{domain.name}</h3>
                                <span className="text-sm font-medium text-gray-500">{domain.weight}% weight</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                                <div className={`${domain.color} h-2 rounded-full`} style={{ width: `${domain.weight}%` }} />
                            </div>
                            <p className="text-sm text-gray-600">{domain.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Scoring Formula */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <Scale className="w-6 h-6 text-primary-600" />
                    Scoring Formula
                </h2>

                <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
                    <div>
                        <h3 className="font-medium text-gray-900 mb-2">Domain Score (0-5 scale)</h3>
                        <code className="block p-3 bg-gray-900 text-green-400 rounded-lg text-sm">
                            domain_score = (points_earned / max_points) × 5
                        </code>
                    </div>

                    <div>
                        <h3 className="font-medium text-gray-900 mb-2">Overall Score (0-100 scale)</h3>
                        <code className="block p-3 bg-gray-900 text-green-400 rounded-lg text-sm">
                            overall_score = Σ (domain_score / 5) × domain_weight
                        </code>
                    </div>

                    <div className="pt-4 border-t border-gray-200">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Question Types:</h4>
                        <ul className="space-y-1 text-sm text-gray-600">
                            <li><strong>Boolean:</strong> Yes = 1 point, No = 0 points</li>
                            <li><strong>Percentage:</strong> Threshold-based scoring (e.g., 95%+ = 1.0, 75%+ = 0.75)</li>
                            <li><strong>Numeric:</strong> Threshold-based scoring with direction (higher or lower is better)</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Maturity Levels */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <TrendingUp className="w-6 h-6 text-primary-600" />
                    Maturity Levels
                </h2>
                <p className="text-gray-600 mb-6">
                    Based on your overall score, AIRS assigns a maturity level that describes
                    your organization's current state of incident response readiness.
                </p>

                <div className="overflow-hidden rounded-xl border border-gray-200">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Level</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Score Range</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Description</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                            {[
                                { level: 1, name: 'Initial', range: '0-20', description: 'Ad-hoc, reactive security posture', color: 'text-red-600' },
                                { level: 2, name: 'Developing', range: '21-40', description: 'Basic controls in place, gaps exist', color: 'text-orange-600' },
                                { level: 3, name: 'Defined', range: '41-60', description: 'Documented processes, consistent execution', color: 'text-yellow-600' },
                                { level: 4, name: 'Managed', range: '61-80', description: 'Measured and controlled, proactive approach', color: 'text-green-600' },
                                { level: 5, name: 'Optimized', range: '81-100', description: 'Continuous improvement, industry-leading', color: 'text-primary-600' },
                            ].map((level) => (
                                <tr key={level.level}>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 font-semibold ${level.color}`}>
                                            {level.level}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 font-medium text-gray-900">{level.name}</td>
                                    <td className="px-4 py-3 text-gray-600">{level.range}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600">{level.description}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}
