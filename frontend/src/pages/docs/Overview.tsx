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
                <div className="flex items-center gap-2 text-primary-605 dark:text-primary-400 mb-4">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Documentation</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    ResilAI Documentation
                </h1>
                <p className="text-xl text-slate-605 dark:text-slate-400 max-w-2xl leading-relaxed">
                    AI Incident Readiness Score — a comprehensive self-assessment tool that evaluates
                    your organization's security posture across five critical domains.
                </p>
            </div>

            {/* What is ResilAI */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    What is ResilAI?
                </h2>
                <div className="prose dark:prose-invert max-w-none">
                    <p className="text-slate-655 dark:text-slate-400 leading-relaxed text-base">
                        ResilAI is an open-source security assessment platform designed to help organizations
                        understand their incident response readiness. By answering 30 targeted questions
                        across 5 security domains, you receive an actionable readiness score,
                        prioritized recommendations, and executive-ready reports.
                    </p>
                </div>
            </section>

            {/* Key Features */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    Key Features
                </h2>
                <div className="grid md:grid-cols-3 gap-6">
                    {[
                        {
                            icon: BarChart3,
                            title: 'Instant Scoring',
                            description: 'Get immediate visibility into your readiness level with weighted domain scores and an overall 0-100 rating.',
                        },
                        {
                            icon: Shield,
                            title: 'Framework Mapping',
                            description: 'Findings automatically map to MITRE ATT&CK, CIS Controls v8, and OWASP Top 10 for compliance alignment.',
                        },
                        {
                            icon: FileText,
                            title: 'Executive Reports',
                            description: 'Generate comprehensive PDF reports with AI-powered narratives and actionable remediation steps.',
                        },
                    ].map((feature) => (
                        <div
                            key={feature.title}
                            className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md"
                        >
                            <feature.icon className="w-8 h-8 text-primary-600 dark:text-primary-400 mb-4" />
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">
                                {feature.title}
                            </h3>
                            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                                {feature.description}
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Quick Start */}
            <section className="p-6 bg-gradient-to-br from-primary-50/40 to-primary-100/40 dark:from-primary-950/20 dark:to-primary-900/10 rounded-3xl border border-primary-100/80 dark:border-primary-900/50 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                <div className="flex flex-col md:flex-row items-start gap-5">
                    <div className="p-3 bg-primary-600 dark:bg-primary-500 rounded-2xl shadow-md flex-shrink-0">
                        <Zap className="w-7 h-7 text-white" />
                    </div>
                    <div className="flex-1">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3 tracking-tight">
                            Quick Start
                        </h2>
                        <ol className="space-y-2.5 text-slate-700 dark:text-slate-305 font-medium">
                            <li className="flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                                <span>Click "Start Assessment" to begin</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                                <span>Answer 30 questions across 5 domains (~5 minutes)</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                                <span>Receive your ResilAI score and maturity level</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                                <span>Download your executive-ready PDF report</span>
                            </li>
                        </ol>
                        <Link
                            to="/assessment/new"
                            className="inline-flex items-center gap-2 mt-6 px-6 py-2.5 bg-primary-600 text-white dark:bg-primary-500 rounded-full hover:bg-primary-700 dark:hover:bg-primary-600 transition-all duration-300 font-semibold shadow-sm hover:shadow"
                        >
                            <span>Start Assessment</span>
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* Documentation Sections */}
            <section>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 tracking-tight">
                    Documentation Sections
                </h2>
                <div className="grid sm:grid-cols-2 gap-4">
                    {[
                        { title: 'Methodology', href: '/docs/methodology', description: 'Scoring domains, weights, and maturity levels' },
                        { title: 'Frameworks', href: '/docs/frameworks', description: 'MITRE ATT&CK, CIS Controls, OWASP mappings' },
                        { title: 'Security', href: '/docs/security', description: 'Authentication, data handling, and privacy' },
                        { title: 'API Reference', href: '/docs/api', description: 'REST API documentation and examples' },
                    ].map((section) => (
                        <Link
                            key={section.title}
                            to={section.href}
                            className="group flex items-center justify-between p-5 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm hover:shadow-md transition-all duration-300 hover:scale-[1.01] hover:border-primary-250 dark:hover:border-primary-800"
                        >
                            <div>
                                <h3 className="font-bold text-slate-900 dark:text-slate-105 group-hover:text-primary-600 dark:group-hover:text-primary-400 text-base transition-colors duration-200">
                                    {section.title}
                                </h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">{section.description}</p>
                            </div>
                            <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-primary-605 dark:group-hover:text-primary-400 transition-all duration-200 transform group-hover:translate-x-1" />
                        </Link>
                    ))}
                </div>
            </section>
        </div>
    );
}
