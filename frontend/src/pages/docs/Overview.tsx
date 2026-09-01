import { Link } from 'react-router-dom';
import {
    ArrowRight,
    Shield,
    BarChart3,
    FileText,
    CheckCircle,
    Zap
} from 'lucide-react';

export default function DocsOverview() {
    return (
        <div className="space-y-12">
            {/* Hero */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-4">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Documentation</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    ResilAI Documentation
                </h1>
                <p className="text-xl text-slate-605 dark:text-slate-400 max-w-3xl leading-relaxed">
                    ResilAI is a Continuous Readiness Operating System. We connect to your existing security, infrastructure, and IT tools to deterministically verify your resilience against disruptions.
                </p>
            </div>

            {/* The ResilAI Loop */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    The Readiness Loop
                </h2>
                <div className="grid md:grid-cols-4 gap-6">
                    {[
                        {
                            icon: Zap,
                            title: '1. Connect',
                            description: 'Integrate your existing tooling (Wazuh, Sentinel, Azure, AWS) in minutes. No agents to deploy.',
                        },
                        {
                            icon: CheckCircle,
                            title: '2. Verify',
                            description: 'The Governance Engine continuously pulls telemetry and verifies it against your regional and industry regulations.',
                        },
                        {
                            icon: BarChart3,
                            title: '3. Understand',
                            description: 'Get an executive-level view of your actual readiness, backed by hard technical evidence rather than self-assessments.',
                        },
                        {
                            icon: FileText,
                            title: '4. Act',
                            description: 'Prioritize remediation efforts based on business criticality, exposure level, and automated AI analysis.',
                        },
                    ].map((step, idx) => (
                        <div
                            key={step.title}
                            className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800/80 shadow-sm relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-50/50 dark:bg-primary-900/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110 duration-500" />
                            <step.icon className="w-8 h-8 text-primary-600 dark:text-primary-400 mb-4" />
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">
                                {step.title}
                            </h3>
                            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                                {step.description}
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Governance Engine */}
            <section className="p-8 bg-gradient-to-br from-primary-50/40 to-primary-100/40 dark:from-primary-950/20 dark:to-primary-900/10 rounded-3xl border border-primary-100/80 dark:border-primary-900/50 shadow-sm">
                <div className="flex flex-col md:flex-row items-start gap-8">
                    <div className="flex-1">
                        <div className="inline-flex items-center justify-center p-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm mb-6 border border-slate-100 dark:border-slate-700">
                            <Shield className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                            The Governance Engine
                        </h2>
                        <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6">
                            Unlike traditional GRC tools that rely on manual self-assessments and point-in-time audits, ResilAI employs a deterministic Governance Engine. It uses a configuration-driven approach to automatically map your organization's unique regional and industry requirements to technical controls.
                        </p>
                        
                        <div className="space-y-4">
                            <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 mt-1">
                                    <div className="w-2 h-2 rounded-full bg-primary-500" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-slate-900 dark:text-slate-100">Deterministic Applicability</h4>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                        Regulations (e.g., GDPR, HIPAA, DORA) are applied automatically based on your organization's physical location, size, and industry.
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 mt-1">
                                    <div className="w-2 h-2 rounded-full bg-primary-500" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-slate-900 dark:text-slate-100">Evidence Verification</h4>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                        The engine translates high-level frameworks (NIST, CIS) into granular technical checks that are verified against live telemetry from your connected systems.
                                    </p>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </section>

            {/* Documentation Sections */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    Explore Documentation
                </h2>
                <div className="grid sm:grid-cols-2 gap-4">
                    {[
                        { title: 'Governance Engine', href: '/docs/governance', description: 'Deep dive into deterministic verification' },
                        { title: 'Frameworks', href: '/docs/frameworks', description: 'Explore supported regulatory and security frameworks' },
                        { title: 'Methodology', href: '/docs/methodology', description: 'Understand how readiness scores are calculated' },
                        { title: 'API Reference', href: '/docs/api', description: 'Integrate directly with our REST API' },
                    ].map((section) => (
                        <Link
                            key={section.title}
                            to={section.href}
                            className="group flex items-center justify-between p-5 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800/80 shadow-sm hover:shadow-md transition-all duration-300 hover:scale-[1.01] hover:border-primary-250 dark:hover:border-primary-800"
                        >
                            <div>
                                <h3 className="font-bold text-slate-900 dark:text-slate-105 group-hover:text-primary-600 dark:group-hover:text-primary-400 text-base transition-colors duration-200">
                                    {section.title}
                                </h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">{section.description}</p>
                            </div>
                            <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-all duration-200 transform group-hover:translate-x-1" />
                        </Link>
                    ))}
                </div>
            </section>
        </div>
    );
}
