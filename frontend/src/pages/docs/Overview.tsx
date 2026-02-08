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
                <div className="flex items-center gap-2 text-primary-600 mb-4">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-medium">Documentation</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    AIRS Documentation
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl">
                    AI Incident Readiness Score — a comprehensive self-assessment tool that evaluates
                    your organization's security posture across five critical domains.
                </p>
            </div>

            {/* What is AIRS */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                    What is AIRS?
                </h2>
                <div className="prose max-w-none">
                    <p className="text-gray-600">
                        AIRS is an open-source security assessment platform designed to help organizations
                        understand their incident response readiness. By answering 30 targeted questions
                        across 5 security domains, you receive an actionable readiness score,
                        prioritized recommendations, and executive-ready reports.
                    </p>
                </div>
            </section>

            {/* Key Features */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
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
                            className="p-6 bg-white rounded-xl border border-gray-200"
                        >
                            <feature.icon className="w-8 h-8 text-primary-600 mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                {feature.title}
                            </h3>
                            <p className="text-gray-600 text-sm">
                                {feature.description}
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Quick Start */}
            <section className="p-6 bg-gradient-to-r from-primary-50 to-primary-100/20 rounded-xl border border-primary-200">
                <div className="flex items-start gap-4">
                    <div className="p-2 bg-primary-600 rounded-lg">
                        <Zap className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            Quick Start
                        </h2>
                        <ol className="space-y-2 text-gray-700">
                            <li className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-primary-600" />
                                Click "Start Assessment" to begin
                            </li>
                            <li className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-primary-600" />
                                Answer 30 questions across 5 domains (~5 minutes)
                            </li>
                            <li className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-primary-600" />
                                Receive your AIRS score and maturity level
                            </li>
                            <li className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-primary-600" />
                                Download your executive-ready PDF report
                            </li>
                        </ol>
                        <Link
                            to="/assessment/new"
                            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                        >
                            Start Assessment
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* Documentation Sections */}
            <section>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
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
                            className="group flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 transition-colors"
                        >
                            <div>
                                <h3 className="font-medium text-gray-900 group-hover:text-primary-600">
                                    {section.title}
                                </h3>
                                <p className="text-sm text-gray-500">{section.description}</p>
                            </div>
                            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
                        </Link>
                    ))}
                </div>
            </section>
        </div>
    );
}
