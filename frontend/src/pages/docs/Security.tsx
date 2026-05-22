import { Lock, Shield, Database, Eye, Clock, CheckCircle } from 'lucide-react';

export default function DocsSecurity() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-605 dark:text-primary-400 mb-4">
                    <Lock className="w-5 h-5" />
                    <span className="text-sm font-semibold tracking-wide uppercase">Security</span>
                </div>
                <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
                    Security & Privacy
                </h1>
                <p className="text-xl text-slate-605 dark:text-slate-400 max-w-2xl leading-relaxed">
                    Learn how ResilAI protects your data, handles authentication,
                    and ensures tenant isolation.
                </p>
            </div>

            {/* Authentication */}
            <section id="authentication">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-blue-50 dark:bg-blue-950/40 rounded-2xl border border-blue-100 dark:border-blue-900/40">
                        <Shield className="w-6 h-6 text-blue-655 dark:text-blue-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        Authentication
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                        ResilAI uses Firebase Authentication for secure user identity management.
                    </p>

                    <ul className="space-y-4">
                        {[
                            { title: 'Email/Password Authentication', desc: 'Secure credential-based login with password hashing' },
                            { title: 'Social Providers', desc: 'Optional Google, Microsoft, and GitHub OAuth integration' },
                            { title: 'MFA Support', desc: 'Multi-factor authentication available for enhanced security' },
                            { title: 'Session Management', desc: 'JWT tokens with configurable expiration and refresh' },
                            { title: 'Public Beta Mode', desc: 'Run assessments in a synthetic-data environment for evaluation' },
                        ].map((item) => (
                            <li key={item.title} className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <span className="font-semibold text-slate-900 dark:text-slate-105 text-base leading-tight">{item.title}</span>
                                    <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">{item.desc}</p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </section>

            {/* Tenant Isolation */}
            <section id="isolation">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-purple-50 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-900/40">
                        <Database className="w-6 h-6 text-purple-655 dark:text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        Tenant Isolation
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                        All data is strictly isolated by organization to prevent cross-tenant access.
                    </p>

                    <div className="grid sm:grid-cols-2 gap-4">
                        <div className="p-5 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-150 dark:border-slate-850 shadow-sm hover:shadow transition-all duration-300 hover:scale-[1.01]">
                            <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-base">Organization Scoping</h3>
                            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                Every assessment, finding, and report is scoped to a specific organization ID.
                            </p>
                        </div>
                        <div className="p-5 bg-slate-50 dark:bg-slate-955 rounded-2xl border border-slate-150 dark:border-slate-850 shadow-sm hover:shadow transition-all duration-300 hover:scale-[1.01]">
                            <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-base">Role-Based Access</h3>
                            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                Users can only access organizations they've been explicitly granted access to.
                            </p>
                        </div>
                        <div className="p-5 bg-slate-50 dark:bg-slate-955 rounded-2xl border border-slate-150 dark:border-slate-850 shadow-sm hover:shadow transition-all duration-300 hover:scale-[1.01]">
                            <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-base">API Enforcement</h3>
                            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                All API endpoints validate organization membership before returning data.
                            </p>
                        </div>
                        <div className="p-5 bg-slate-50 dark:bg-slate-955 rounded-2xl border border-slate-150 dark:border-slate-850 shadow-sm hover:shadow transition-all duration-300 hover:scale-[1.01]">
                            <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-base">Audit Logging</h3>
                            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                Access attempts are logged for security monitoring and compliance.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Data Storage */}
            <section id="storage">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-green-50 dark:bg-green-955/40 rounded-2xl border border-green-100 dark:border-green-900/40">
                        <Database className="w-6 h-6 text-green-655 dark:text-green-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        Data Storage
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <p className="text-slate-655 dark:text-slate-455 mb-6 leading-relaxed">
                        ResilAI stores data securely in Google Cloud infrastructure.
                    </p>

                    <div className="overflow-hidden rounded-2xl border border-slate-150 dark:border-slate-800 shadow-sm">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-slate-50 dark:bg-slate-950 border-b border-slate-150 dark:border-slate-800">
                                    <tr>
                                        <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Data Type</th>
                                        <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Storage</th>
                                        <th className="px-5 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Encryption</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-150 dark:divide-slate-850 bg-white dark:bg-slate-900">
                                    {[
                                        { type: 'User Accounts', storage: 'Firebase Auth', encryption: 'At rest & in transit' },
                                        { type: 'Organizations', storage: 'Firestore', encryption: 'At rest & in transit' },
                                        { type: 'Assessments', storage: 'Firestore', encryption: 'At rest & in transit' },
                                        { type: 'PDF Reports', storage: 'Cloud Storage', encryption: 'At rest & in transit' },
                                    ].map((row) => (
                                        <tr key={row.type} className="transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                                            <td className="px-5 py-4 font-semibold text-slate-900 dark:text-slate-100">{row.type}</td>
                                            <td className="px-5 py-4 text-slate-600 dark:text-slate-400 font-medium">{row.storage}</td>
                                            <td className="px-5 py-4 text-slate-600 dark:text-slate-400 font-medium">{row.encryption}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            {/* Data Retention */}
            <section id="retention">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-orange-50 dark:bg-orange-955/40 rounded-2xl border border-orange-100 dark:border-orange-900/40">
                        <Clock className="w-6 h-6 text-orange-655 dark:text-orange-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        Data Retention
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <ul className="space-y-4 font-medium text-slate-600 dark:text-slate-405 text-sm">
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Assessment data is retained until explicitly deleted by the user.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Users can request data export or deletion at any time.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Deleted organizations and their data are permanently removed.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Public Beta synthetic assessments can be isolated from production persistence.</span>
                        </li>
                    </ul>
                </div>
            </section>

            {/* Privacy */}
            <section id="privacy">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-red-50 dark:bg-red-955/40 rounded-2xl border border-red-100 dark:border-red-900/40">
                        <Eye className="w-6 h-6 text-red-655 dark:text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        Privacy
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-150 dark:border-slate-800/80 shadow-sm transition-all duration-300 hover:scale-[1.01] hover:shadow-md">
                    <ul className="space-y-4 font-medium text-slate-600 dark:text-slate-405 text-sm">
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">No assessment data is shared with third parties.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Anonymized analytics may be collected for product improvement (opt-out available).</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">AI report generation uses Google Gemini with data not retained for training.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">Self-hosted deployment option for maximum data control.</span>
                        </li>
                    </ul>
                </div>
            </section>
        </div>
    );
}
