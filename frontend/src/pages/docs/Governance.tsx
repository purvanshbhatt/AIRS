import { Link } from 'react-router-dom';
import {
    ArrowRight,
    Shield,
    CheckCircle,
    Database,
    Zap,
    Scale
} from 'lucide-react';

export default function DocsGovernance() {
    return (
        <div className="space-y-12">
            <div>
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-4">
                    <Scale className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Documentation / Engine</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    The Governance Engine
                </h1>
                <p className="text-xl text-slate-605 dark:text-slate-400 max-w-3xl leading-relaxed">
                    ResilAI replaces point-in-time compliance audits and self-assessments with a deterministic, configuration-driven Governance Engine that maps organizational context to real-time technical evidence.
                </p>
            </div>

            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    Deterministic Organization Profiles
                </h2>
                <div className="prose dark:prose-invert max-w-none">
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-base mb-6">
                        Organizations no longer manually select which compliance frameworks they need to adhere to. Instead, ResilAI calculates <strong>regulatory applicability</strong> automatically during onboarding based on three key vectors:
                    </p>
                    
                    <div className="grid md:grid-cols-3 gap-6 my-8">
                        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">Location</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400">Determines geopolitical regulations such as GDPR (EU), CCPA (California, US), and DORA (EU Financial Sector).</p>
                        </div>
                        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">Industry</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400">Applies sector-specific controls like HIPAA (Healthcare), PCI-DSS (Retail/Finance), and NERC CIP (Energy).</p>
                        </div>
                        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">Size</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400">Scales the required maturity level and scopes exemptions based on organizational headcount or revenue.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    How Verification Works
                </h2>
                
                <div className="space-y-6">
                    <div className="flex gap-4 p-6 bg-slate-50 dark:bg-slate-900/50 rounded-3xl border border-slate-100 dark:border-slate-800">
                        <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 flex items-center justify-center">
                                1
                            </div>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">Policy Mapping</h3>
                            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                                High-level frameworks (e.g., NIST CSF 2.0) are translated into discrete <strong>Control Rules</strong>. These rules dictate exactly what technical conditions must be met to satisfy a compliance requirement.
                            </p>
                        </div>
                    </div>

                    <div className="flex gap-4 p-6 bg-slate-50 dark:bg-slate-900/50 rounded-3xl border border-slate-100 dark:border-slate-800">
                        <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 text-purple-600 flex items-center justify-center">
                                2
                            </div>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">Telemetry Ingestion</h3>
                            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                                Connectors (Wazuh, Sentinel, Entra ID) stream real-time operational state into the platform. This raw data is normalized into a standard event schema.
                            </p>
                        </div>
                    </div>

                    <div className="flex gap-4 p-6 bg-slate-50 dark:bg-slate-900/50 rounded-3xl border border-slate-100 dark:border-slate-800">
                        <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/50 text-green-600 flex items-center justify-center">
                                3
                            </div>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">Deterministic Evaluation</h3>
                            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                                The Governance Engine evaluates the ingested telemetry against the Control Rules. If the technical evidence satisfies the rule's conditions, the control is marked <strong>Compliant</strong>. The result is immutable and cryptographically logged for auditability.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="pt-8 border-t border-slate-100 dark:border-slate-800">
                <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                    <Link
                        to="/docs/methodology"
                        className="flex items-center gap-2 text-slate-500 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                    >
                        <span>Methodology</span>
                    </Link>
                    <Link
                        to="/docs/frameworks"
                        className="flex items-center gap-2 text-slate-500 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                    >
                        <span>Frameworks</span>
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>
            </section>
        </div>
    );
}
