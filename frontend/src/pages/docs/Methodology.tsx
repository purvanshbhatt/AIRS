import { BarChart3, Scale, Target, TrendingUp, Info } from 'lucide-react';

export default function DocsMethodology() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-605 dark:text-primary-400 mb-4">
                    <BarChart3 className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Methodology</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    Scoring Methodology
                </h1>
                <p className="text-lg text-slate-605 dark:text-slate-400 max-w-2xl leading-relaxed">
                    Learn how ResilAI calculates readiness scores across five security domains
                    and determines organizational maturity levels.
                </p>
            </div>

            {/* Domains */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3 tracking-tight">
                    <Target className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                    <span>Assessment Domains</span>
                </h2>
                <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                    ResilAI evaluates your security posture across five critical domains, each with
                    a specific weight reflecting its importance in incident response readiness.
                </p>

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
                            className="p-5 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md flex flex-col justify-between"
                        >
                            <div>
                                <div className="flex items-start justify-between gap-2 mb-3">
                                    <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base leading-tight">{domain.name}</h3>
                                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-850 flex-shrink-0">{domain.weight}% weight</span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-950 rounded-full h-2 mb-4 overflow-hidden border border-slate-200/40 dark:border-slate-900/60">
                                    <div className={`${domain.color} h-2 rounded-full`} style={{ width: `${domain.weight}%` }} />
                                </div>
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{domain.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* How Domain Weights Are Determined */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3 tracking-tight">
                    <Info className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                    <span>How Domain Weights Are Determined</span>
                </h2>
                <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                    Domain weights are not arbitrary — they are derived from four evidence-based factors
                    that reflect real-world incident impact and regulatory expectations.
                </p>

                <div className="grid sm:grid-cols-2 gap-4 mb-6">
                    <div className="p-5 bg-red-50/50 dark:bg-red-950/20 rounded-3xl border border-red-200/85 dark:border-red-900/50 shadow-sm transition-all duration-300 hover:scale-[1.01]">
                        <h4 className="font-bold text-red-900 dark:text-red-305 mb-2 text-base">MITRE ATT&CK Prevalence</h4>
                        <p className="text-xs text-red-805 dark:text-red-400 leading-relaxed">
                            Domains covering the most frequently observed attacker techniques (per MITRE
                            data and threat intelligence) receive higher weight. Detection and telemetry
                            cover the widest range of T-codes.
                        </p>
                    </div>
                    <div className="p-5 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-3xl border border-emerald-200/85 dark:border-emerald-900/50 shadow-sm transition-all duration-300 hover:scale-[1.01]">
                        <h4 className="font-bold text-emerald-900 dark:text-emerald-305 mb-2 text-base">NIST CSF Function Criticality</h4>
                        <p className="text-xs text-emerald-805 dark:text-emerald-400 leading-relaxed">
                            Each domain aligns to a NIST CSF 2.0 lifecycle function (Detect, Protect, Respond,
                            Recover). Functions that span more CSF categories receive proportionally greater
                            weight to ensure lifecycle coverage.
                        </p>
                    </div>
                    <div className="p-5 bg-blue-50/50 dark:bg-blue-950/20 rounded-3xl border border-blue-200/85 dark:border-blue-900/50 shadow-sm transition-all duration-300 hover:scale-[1.01]">
                        <h4 className="font-bold text-blue-900 dark:text-blue-305 mb-2 text-base">Breach Root-Cause Analysis</h4>
                        <p className="text-xs text-blue-805 dark:text-blue-400 leading-relaxed">
                            Weights reflect confirmed breach enablers from CISA advisories, FBI IC3 reports,
                            and the Verizon DBIR. Telemetry and detection gaps are implicated in a majority
                            of successful ransomware incidents.
                        </p>
                    </div>
                    <div className="p-5 bg-amber-50/50 dark:bg-amber-955/20 rounded-3xl border border-amber-200/85 dark:border-amber-900/50 shadow-sm transition-all duration-300 hover:scale-[1.01]">
                        <h4 className="font-bold text-amber-900 dark:text-amber-305 mb-2 text-base">Regulatory Exposure</h4>
                        <p className="text-xs text-amber-805 dark:text-amber-400 leading-relaxed">
                            Domains with direct compliance implications (identity access controls, audit
                            logging, incident response documentation) are weighted to reflect obligations
                            under SEC, HIPAA, PCI-DSS, and NIS2 frameworks.
                        </p>
                    </div>
                </div>

                {/* Weight Distribution Visual */}
                <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <h4 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-4">Weight Distribution Details:</h4>
                    <div className="space-y-4">
                        {[
                            { name: 'Telemetry & Logging', weight: 25, function: 'DE', color: 'bg-blue-500', reason: 'Highest ATT&CK coverage; forensic prerequisite for all downstream detection' },
                            { name: 'Detection Coverage', weight: 20, function: 'DE', color: 'bg-green-500', reason: 'Primary defense against active intrusion; EDR is the #1 ransomware preventive' },
                            { name: 'Identity Visibility', weight: 20, function: 'PR', color: 'bg-purple-500', reason: 'Credential compromise is the leading initial access vector (DBIR, IC3)' },
                            { name: 'Backup/Recovery', weight: 20, function: 'RC', color: 'bg-red-500', reason: 'Operational resilience; ransomware recovery without payment depends on this' },
                            { name: 'IR Playbooks', weight: 15, function: 'RS', color: 'bg-orange-500', reason: 'Response coordination; lower weight reflects dependence on other controls' },
                        ].map((d) => (
                            <div key={d.name} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                                <div className="w-48 text-sm font-semibold text-slate-700 dark:text-slate-205 truncate" title={d.name}>{d.name}</div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 h-3 bg-slate-150 dark:bg-slate-950 rounded-full overflow-hidden border border-slate-200/30 dark:border-slate-900/60">
                                            <div className={`h-full ${d.color} rounded-full`} style={{ width: `${d.weight}%` }} />
                                        </div>
                                        <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 w-10 text-right">{d.weight}%</span>
                                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-md text-slate-500 dark:text-slate-400 w-10 text-center">{d.function}</span>
                                    </div>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">{d.reason}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-405 mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 leading-relaxed">
                        Weights sum to 100%. They are applied multiplicatively to each domain's 0–5 raw score
                        to produce the overall 0–100 Risk Posture index. Weights are reviewed quarterly against
                        updated threat intelligence.
                    </p>
                </div>
            </section>

            {/* Scoring Formula */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3 tracking-tight">
                    <Scale className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                    <span>Scoring Formula</span>
                </h2>

                <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800 shadow-sm space-y-5">
                    <div>
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2 text-base">Domain Score (0-5 scale)</h3>
                        <code className="block p-4 bg-slate-950 dark:bg-black text-emerald-400 rounded-2xl text-xs sm:text-sm font-mono shadow-inner border border-slate-900 dark:border-slate-950 overflow-x-auto">
                            domain_score = (points_earned / max_points) × 5
                        </code>
                    </div>

                    <div>
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2 text-base">Overall Score (0-100 scale)</h3>
                        <code className="block p-4 bg-slate-950 dark:bg-black text-emerald-400 rounded-2xl text-xs sm:text-sm font-mono shadow-inner border border-slate-900 dark:border-slate-950 overflow-x-auto">
                            overall_score = Σ (domain_score / 5) × domain_weight
                        </code>
                    </div>

                    <div className="pt-5 border-t border-slate-200 dark:border-slate-805">
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2.5">Question Types & Evaluation:</h4>
                        <ul className="space-y-2 text-sm text-slate-655 dark:text-slate-400 font-medium">
                            <li className="flex items-start gap-2.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary-605 mt-2 flex-shrink-0" />
                                <span><strong>Boolean:</strong> Direct matching where Yes = 1 point, No = 0 points.</span>
                            </li>
                            <li className="flex items-start gap-2.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary-605 mt-2 flex-shrink-0" />
                                <span><strong>Percentage:</strong> Threshold-based scoring distributions (e.g., 95%+ = 1.0, 75%+ = 0.75).</span>
                            </li>
                            <li className="flex items-start gap-2.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary-605 mt-2 flex-shrink-0" />
                                <span><strong>Numeric:</strong> Threshold-based scoring with directional target controls (higher or lower based on context).</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Maturity Levels */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3 tracking-tight">
                    <TrendingUp className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                    <span>Maturity Levels</span>
                </h2>
                <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                    Based on your overall score, ResilAI assigns a maturity level that describes
                    your organization's current state of incident response readiness.
                </p>

                <div className="overflow-hidden rounded-3xl border border-slate-150 dark:border-slate-800 shadow-sm">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-150 dark:border-slate-800">
                                <tr>
                                    <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Level</th>
                                    <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
                                    <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Score Range</th>
                                    <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Description</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-150 dark:divide-slate-805 bg-white dark:bg-slate-950">
                                {[
                                    { level: 1, name: 'Initial', range: '0-20', description: 'Ad-hoc, reactive security posture', color: 'text-red-650 bg-red-50 dark:bg-red-955/20 border-red-100 dark:border-red-900/40' },
                                    { level: 2, name: 'Developing', range: '21-40', description: 'Basic controls in place, gaps exist', color: 'text-orange-650 bg-orange-50 dark:bg-orange-955/20 border-orange-105 dark:border-orange-900/40' },
                                    { level: 3, name: 'Defined', range: '41-60', description: 'Documented processes, consistent execution', color: 'text-yellow-650 bg-yellow-50 dark:bg-yellow-955/20 border-yellow-105 dark:border-yellow-900/40' },
                                    { level: 4, name: 'Managed', range: '61-80', description: 'Measured and controlled, proactive approach', color: 'text-green-650 bg-green-50 dark:bg-green-955/20 border-green-105 dark:border-green-900/40' },
                                    { level: 5, name: 'Optimized', range: '81-100', description: 'Continuous improvement, industry-leading', color: 'text-primary-605 bg-primary-50 dark:bg-primary-955/20 border-primary-105 dark:border-primary-900/40' },
                                ].map((level) => (
                                    <tr key={level.level} className="transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                                        <td className="px-5 py-4">
                                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full border text-sm font-bold ${level.color} shadow-sm`}>
                                                {level.level}
                                            </span>
                                        </td>
                                        <td className="px-5 py-4 font-semibold text-slate-900 dark:text-slate-100">{level.name}</td>
                                        <td className="px-5 py-4 font-mono text-sm text-slate-600 dark:text-slate-400 font-semibold">{level.range}</td>
                                        <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-400 font-medium">{level.description}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
        </div>
    );
}
