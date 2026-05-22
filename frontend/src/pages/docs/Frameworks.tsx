import React, { useState } from 'react';
import { Shield, ExternalLink, AlertTriangle, CheckCircle, RefreshCw, Eye, EyeOff, Zap, Scale, Brain, Clock } from 'lucide-react';
import { useDemoMode } from '../../contexts';

export default function DocsFrameworks() {
    const { systemStatus } = useDemoMode();
    const isStaging = systemStatus?.environment === 'staging';
    const [showFuture, setShowFuture] = useState(false);

    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-605 dark:text-primary-400 mb-4">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Frameworks</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    Security Framework Mappings
                </h1>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
                        ResilAI findings automatically map to industry-standard security frameworks,
                        enabling compliance alignment and standardized remediation.
                    </p>
                    {isStaging && (
                        <button
                            onClick={() => setShowFuture(!showFuture)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-300 border shadow-sm hover:shadow-md ${
                                showFuture
                                    ? 'bg-purple-50 text-purple-750 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-900/60'
                                    : 'bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800'
                            }`}
                        >
                            {showFuture ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            <span>{showFuture ? 'Hide' : 'Show'} Future Regulations</span>
                            <span className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900 text-purple-750 dark:text-purple-300 rounded-full font-bold">
                                STAGING
                            </span>
                        </button>
                    )}
                </div>
            </div>

            {/* MITRE ATT&CK */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-red-50 dark:bg-red-950/40 rounded-2xl border border-red-100 dark:border-red-900/40">
                        <AlertTriangle className="w-6 h-6 text-red-650 dark:text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        MITRE ATT&CK
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-650 dark:text-slate-455 mb-6 leading-relaxed">
                        Findings map to specific ATT&CK techniques that adversaries may exploit when
                        security controls are missing. This helps security teams understand the real-world
                        attack behaviors enabled by identified gaps.
                    </p>

                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 text-base">Mapped Tactics:</h3>
                    <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                        {[
                            'Credential Access', 'Persistence', 'Privilege Escalation',
                            'Defense Evasion', 'Discovery', 'Lateral Movement',
                            'Collection', 'Command and Control', 'Exfiltration',
                            'Impact', 'Initial Access', 'Execution'
                        ].map((tactic) => (
                            <div key={tactic} className="flex items-center gap-2.5 text-sm text-slate-600 dark:text-slate-400 font-medium">
                                <CheckCircle className="w-4.5 h-4.5 text-green-500 flex-shrink-0" />
                                <span>{tactic}</span>
                            </div>
                        ))}
                    </div>

                    <a
                        href="https://attack.mitre.org/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline font-semibold"
                    >
                        Learn more about MITRE ATT&CK
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* CIS Controls */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-blue-50 dark:bg-blue-950/40 rounded-2xl border border-blue-100 dark:border-blue-900/40">
                        <Shield className="w-6 h-6 text-blue-655 dark:text-blue-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        CIS Controls v8
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                        Findings map to specific CIS Controls, with Implementation Group (IG) classification
                        to help prioritize based on organizational maturity level.
                    </p>

                    <div className="grid md:grid-cols-3 gap-4 mb-6">
                        <div className="p-4 bg-green-50/50 dark:bg-green-950/30 rounded-2xl border border-green-200/80 dark:border-green-900/60 shadow-sm hover:shadow transition-shadow duration-300">
                            <h4 className="font-semibold text-green-900 dark:text-green-300 mb-1">IG1 - Basic Cyber Hygiene</h4>
                            <p className="text-xs text-green-805 dark:text-green-400 leading-relaxed">Essential controls for all organizations. Minimum baseline for security.</p>
                        </div>
                        <div className="p-4 bg-yellow-50/50 dark:bg-yellow-950/30 rounded-2xl border border-yellow-200/80 dark:border-yellow-900/60 shadow-sm hover:shadow transition-shadow duration-300">
                            <h4 className="font-semibold text-yellow-900 dark:text-yellow-300 mb-1">IG2 - Enhanced Controls</h4>
                            <p className="text-xs text-yellow-805 dark:text-yellow-400 leading-relaxed">For organizations handling sensitive data. Builds on IG1.</p>
                        </div>
                        <div className="p-4 bg-red-50/50 dark:bg-red-950/30 rounded-2xl border border-red-200/80 dark:border-red-900/60 shadow-sm hover:shadow transition-shadow duration-300">
                            <h4 className="font-semibold text-red-900 dark:text-red-300 mb-1">IG3 - Advanced Controls</h4>
                            <p className="text-xs text-red-805 dark:text-red-400 leading-relaxed">For high-value targets facing sophisticated adversaries.</p>
                        </div>
                    </div>

                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 text-base">Key Control Areas:</h3>
                    <ul className="grid sm:grid-cols-2 gap-2.5 text-sm text-slate-655 dark:text-slate-400 font-medium">
                        {[
                            'Control 5: Account Management',
                            'Control 6: Access Control Management',
                            'Control 8: Audit Log Management',
                            'Control 10: Malware Defenses',
                            'Control 11: Data Recovery',
                            'Control 13: Network Monitoring',
                            'Control 17: Incident Response',
                        ].map((control) => (
                            <li key={control} className="flex items-center gap-2.5">
                                <CheckCircle className="w-4.5 h-4.5 text-blue-500 flex-shrink-0" />
                                <span>{control}</span>
                            </li>
                        ))}
                    </ul>

                    <a
                        href="https://www.cisecurity.org/controls"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 mt-6 text-primary-600 dark:text-primary-400 hover:underline font-semibold"
                    >
                        Learn more about CIS Controls
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* OWASP */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-purple-50 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-900/40">
                        <Shield className="w-6 h-6 text-purple-655 dark:text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        OWASP Top 10
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
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
                                className={`p-4 rounded-2xl border transition-all duration-300 hover:scale-[1.01] ${
                                    item.relevant
                                        ? 'bg-purple-50/50 dark:bg-purple-950/30 border-purple-205 dark:border-purple-900/60 shadow-sm'
                                        : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 shadow-sm'
                                }`}
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-mono font-bold text-purple-600 dark:text-purple-400">{item.id}</span>
                                    {item.relevant && (
                                        <span className="text-xs px-2 py-0.5 bg-purple-200 dark:bg-purple-800 text-purple-750 dark:text-purple-300 rounded-full font-semibold">
                                            Mapped
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-slate-700 dark:text-slate-300 font-semibold">{item.name}</p>
                            </div>
                        ))}
                    </div>

                    <a
                        href="https://owasp.org/Top10/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline font-semibold"
                    >
                        Learn more about OWASP Top 10
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* NIST CSF 2.0 */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-teal-50 dark:bg-teal-950/40 rounded-2xl border border-teal-100 dark:border-teal-900/40">
                        <Shield className="w-6 h-6 text-teal-655 dark:text-teal-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        NIST Cybersecurity Framework 2.0
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                        Every assessment question maps to one of the six NIST CSF 2.0 lifecycle functions,
                        providing end-to-end coverage across the cybersecurity risk management lifecycle.
                        This ensures findings address governance, prevention, detection, and recovery equally.
                    </p>

                    {/* Lifecycle Diagram */}
                    <div className="mb-6">
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-4 text-base">CSF 2.0 Lifecycle Functions:</h3>
                        <div className="flex flex-wrap items-center justify-center gap-3 mb-6 bg-slate-50 dark:bg-slate-950 p-6 rounded-3xl border border-slate-150 dark:border-slate-900/50">
                            {[
                                { code: 'GV', name: 'Govern', color: 'bg-slate-105 dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-205 dark:border-slate-800', description: 'Establish and monitor cybersecurity risk management strategy, expectations, and policy' },
                                { code: 'ID', name: 'Identify', color: 'bg-blue-50 dark:bg-blue-950/40 text-blue-750 dark:text-blue-300 border-blue-205 dark:border-blue-900/60', description: 'Understand organizational context, assets, and risk to prioritize efforts' },
                                { code: 'PR', name: 'Protect', color: 'bg-green-50 dark:bg-green-950/40 text-green-755 dark:text-green-300 border-green-205 dark:border-green-900/60', description: 'Implement safeguards to ensure delivery of critical services' },
                                { code: 'DE', name: 'Detect', color: 'bg-amber-50 dark:bg-amber-950/40 text-amber-755 dark:text-amber-300 border-amber-205 dark:border-amber-900/60', description: 'Identify the occurrence of cybersecurity events in a timely manner' },
                                { code: 'RS', name: 'Respond', color: 'bg-orange-50 dark:bg-orange-950/40 text-orange-755 dark:text-orange-300 border-orange-205 dark:border-orange-900/60', description: 'Take action regarding a detected cybersecurity incident' },
                                { code: 'RC', name: 'Recover', color: 'bg-purple-50 dark:bg-purple-950/40 text-purple-755 dark:text-purple-300 border-purple-205 dark:border-purple-900/60', description: 'Restore capabilities or services impaired by a cybersecurity incident' },
                            ].map((func, index) => (
                                <React.Fragment key={func.code}>
                                    <div className={`px-4 py-3 rounded-2xl border ${func.color} text-center min-w-[105px] shadow-sm transition-all duration-300 hover:scale-105`}>
                                        <div className="text-xl font-bold font-mono">{func.code}</div>
                                        <div className="text-xs font-semibold mt-0.5">{func.name}</div>
                                    </div>
                                    {index < 5 && (
                                        <RefreshCw className="w-4 h-4 text-slate-300 dark:text-slate-700 hidden lg:block" />
                                    )}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>

                    {/* Function Details */}
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                        {[
                            { code: 'GV', name: 'Govern', desc: 'Establish and monitor cybersecurity risk management strategy, expectations, and policy.', color: 'border-slate-150 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/30' },
                            { code: 'ID', name: 'Identify', desc: 'Understand organizational context, assets, and risk to prioritize cybersecurity efforts.', color: 'border-blue-150 dark:border-blue-900/60 bg-blue-50/50 dark:bg-blue-950/30' },
                            { code: 'PR', name: 'Protect', desc: 'Implement safeguards such as MFA, PAM, and access controls to ensure delivery of services.', color: 'border-green-150 dark:border-green-900/60 bg-green-50/50 dark:bg-green-950/30' },
                            { code: 'DE', name: 'Detect', desc: 'Identify cybersecurity events through EDR, log monitoring, and alert triage processes.', color: 'border-amber-150 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/30' },
                            { code: 'RS', name: 'Respond', desc: 'Take action on detected incidents through IR playbooks, communication plans, and containment.', color: 'border-orange-150 dark:border-orange-900/60 bg-orange-50/50 dark:bg-orange-950/30' },
                            { code: 'RC', name: 'Recover', desc: 'Restore impaired capabilities via backup recovery, RTO targets, and DR planning.', color: 'border-purple-150 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/30' },
                        ].map((func) => (
                            <div key={func.code} className={`p-4 rounded-2xl border transition-all duration-300 hover:scale-[1.01] ${func.color}`}>
                                <div className="flex items-center gap-2 mb-1.5">
                                    <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-205">{func.code}</span>
                                    <span className="font-bold text-sm text-slate-900 dark:text-slate-100">{func.name}</span>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{func.desc}</p>
                            </div>
                        ))}
                    </div>

                    {/* Domain Mapping */}
                    <div className="p-5 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-850 mb-6">
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
                            How Assessment Domains Map to NIST CSF 2.0:
                        </h4>
                        <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400 font-medium">
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-amber-705 dark:text-amber-300">DE</span>
                                <span>Telemetry &amp; Logging — Detect: Continuous Monitoring (DE.CM)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-amber-705 dark:text-amber-300">DE</span>
                                <span>Detection Coverage — Detect: Adverse Event Analysis (DE.AE)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-green-705 dark:text-green-300">PR</span>
                                <span>Identity Visibility — Protect: Identity Management &amp; Access Control (PR.AA)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-orange-705 dark:text-orange-300">RS</span>
                                <span>IR Playbooks &amp; Process — Respond: Incident Management (RS.MA)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="inline-block w-8 text-xs font-mono font-bold text-purple-755 dark:text-purple-300">RC</span>
                                <span>Backup/Recovery &amp; Resilience — Recover: Incident Recovery Plan Execution (RC.RP)</span>
                            </div>
                        </div>
                    </div>

                    <a
                        href="https://www.nist.gov/cyberframework"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline font-semibold"
                    >
                        Learn more about NIST CSF 2.0
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
            </section>

            {/* Future Regulations — Staging Only */}
            {isStaging && showFuture && (
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2.5 bg-purple-50 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-900/40">
                            <Zap className="w-6 h-6 text-purple-650 dark:text-purple-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                            Future Regulations
                        </h2>
                        <span className="px-2.5 py-0.5 text-xs bg-purple-200 dark:bg-purple-800 text-purple-755 dark:text-purple-300 rounded-full font-bold">
                            PREVIEW
                        </span>
                    </div>

                    <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-purple-100 dark:border-purple-900/60 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                        <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                            Upcoming regulatory frameworks that will impact organizational compliance posture.
                            ResilAI is mapping assessment domains to predicted regulatory requirements for
                            proactive gap analysis.
                        </p>

                        {/* EU AI Act */}
                        <div className="mb-6 p-4 bg-purple-50/50 dark:bg-purple-950/30 rounded-2xl border border-purple-200/80 dark:border-purple-900/60 shadow-sm">
                            <div className="flex flex-wrap items-center gap-3 mb-3">
                                <Brain className="w-5 h-5 text-purple-605 dark:text-purple-400" />
                                <h3 className="font-semibold text-slate-900 dark:text-slate-100">EU Artificial Intelligence Act</h3>
                                <span className="text-xs px-2.5 py-0.5 bg-yellow-100 dark:bg-yellow-950/50 text-yellow-805 dark:text-yellow-300 rounded-full font-bold">
                                    Effective Aug 2025
                                </span>
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                                The EU AI Act establishes a risk-based regulatory framework for AI systems.
                                Organizations deploying high-risk AI must demonstrate conformity assessments,
                                transparency obligations, and human oversight requirements.
                            </p>

                            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-205 mb-3">
                                Predicted Gap Areas for AIRS Organizations:
                            </h4>
                            <div className="grid sm:grid-cols-2 gap-3 mb-4">
                                {[
                                    { area: 'AI Model Inventory', gap: 'Shadow AI detection gaps', risk: 'high' },
                                    { area: 'Data Governance', gap: 'Training data provenance tracking', risk: 'high' },
                                    { area: 'Risk Classification', gap: 'AI system risk tier classification', risk: 'medium' },
                                    { area: 'Transparency', gap: 'Model explainability documentation', risk: 'medium' },
                                    { area: 'Human Oversight', gap: 'Automated decision review processes', risk: 'high' },
                                    { area: 'Monitoring', gap: 'Post-deployment AI performance monitoring', risk: 'low' },
                                ].map((item) => (
                                    <div key={item.area} className={`p-3.5 rounded-2xl border text-sm transition-all duration-300 hover:scale-[1.01] shadow-sm ${
                                        item.risk === 'high' ? 'border-red-200 dark:border-red-900/60 bg-red-50/50 dark:bg-red-950/20' :
                                        item.risk === 'medium' ? 'border-yellow-200 dark:border-yellow-900/60 bg-yellow-50/50 dark:bg-yellow-950/20' :
                                        'border-green-200 dark:border-green-900/60 bg-green-50/50 dark:bg-green-950/20'
                                    }`}>
                                        <div className="font-semibold text-slate-850 dark:text-slate-200">{item.area}</div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">{item.gap}</div>
                                    </div>
                                ))}
                            </div>

                            <a
                                href="https://artificialintelligenceact.eu/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline text-sm font-semibold"
                            >
                                Learn more about EU AI Act
                                <ExternalLink className="w-3 h-3" />
                            </a>
                        </div>

                        {/* DORA */}
                        <div className="mb-6 p-4 bg-blue-50/50 dark:bg-blue-950/30 rounded-2xl border border-blue-200/80 dark:border-blue-900/60 shadow-sm">
                            <div className="flex flex-wrap items-center gap-3 mb-3">
                                <Scale className="w-5 h-5 text-blue-605 dark:text-blue-400" />
                                <h3 className="font-semibold text-slate-900 dark:text-slate-100">DORA — Digital Operational Resilience Act</h3>
                                <span className="text-xs px-2.5 py-0.5 bg-green-105 dark:bg-green-950/50 text-green-805 dark:text-green-300 rounded-full font-bold">
                                    Effective Jan 2025
                                </span>
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                                EU regulation for financial sector ICT risk management, requiring continuous
                                operational resilience testing and third-party risk management. AIRS GHI scoring
                                maps directly to DORA&apos;s ICT risk management framework.
                            </p>
                            <div className="grid sm:grid-cols-3 gap-2.5">
                                {[
                                    'ICT Risk Management',
                                    'Incident Reporting',
                                    'Resilience Testing',
                                    'Third-Party Risk',
                                    'Information Sharing',
                                    'Oversight Framework',
                                ].map((pillar) => (
                                    <div key={pillar} className="flex items-center gap-2 text-xs text-slate-650 dark:text-slate-400 font-medium">
                                        <CheckCircle className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                                        <span>{pillar}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* NIS2 Directive */}
                        <div className="p-4 bg-teal-50/50 dark:bg-teal-950/30 rounded-2xl border border-teal-200/80 dark:border-teal-900/60 shadow-sm">
                            <div className="flex flex-wrap items-center gap-3 mb-3">
                                <Shield className="w-5 h-5 text-teal-605 dark:text-teal-400" />
                                <h3 className="font-semibold text-slate-900 dark:text-slate-100">NIS2 Directive</h3>
                                <span className="text-xs px-2.5 py-0.5 bg-green-105 dark:bg-green-950/50 text-green-805 dark:text-green-300 rounded-full font-bold">
                                    Effective Oct 2024
                                </span>
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                                Expanded EU cybersecurity directive covering essential and important entities.
                                Requires supply chain security, incident response within 24 hours, and
                                management body accountability — all areas tracked by AIRS assessments.
                            </p>
                            <div className="grid sm:grid-cols-2 gap-2.5">
                                {[
                                    { label: 'Risk Assessment', mapped: true },
                                    { label: 'Incident Handling', mapped: true },
                                    { label: 'Business Continuity', mapped: true },
                                    { label: 'Supply Chain Security', mapped: false },
                                ].map((item) => (
                                    <div key={item.label} className="flex items-center gap-2 text-xs text-slate-650 dark:text-slate-400 font-medium">
                                        {item.mapped ? <CheckCircle className="w-3.5 h-3.5 text-teal-500 flex-shrink-0" /> : <Clock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />}
                                        <span>{item.label}</span>
                                        {!item.mapped && <span className="text-xs text-slate-405 dark:text-slate-500 font-normal">(planned)</span>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>
            )}

            {/* How It Works */}
            <section className="p-6 bg-slate-50 dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    How Framework Mapping Works
                </h2>
                <ol className="space-y-4 text-slate-600 dark:text-slate-400 font-medium">
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white dark:bg-primary-500 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">1</span>
                        <span className="mt-0.5">Each assessment question is linked to potential security gaps (finding rules)</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white dark:bg-primary-500 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">2</span>
                        <span className="mt-0.5">Finding rules map to specific framework references (MITRE techniques, CIS controls, OWASP categories)</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white dark:bg-primary-500 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">3</span>
                        <span className="mt-0.5">Your report includes framework references for each identified gap</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white dark:bg-primary-500 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">4</span>
                        <span className="mt-0.5">Use this information for compliance reporting and prioritized remediation</span>
                    </li>
                </ol>
            </section>
        </div>
    );
}
