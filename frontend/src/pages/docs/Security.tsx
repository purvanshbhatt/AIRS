import { Lock, Shield, Database, Eye, Clock, CheckCircle } from 'lucide-react';

export default function DocsSecurity() {
    return (
        <div className="space-y-12">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 mb-4">
                    <Lock className="w-5 h-5" />
                    <span className="text-sm font-medium">Security</span>
                </div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    Security & Privacy
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl">
                    Learn how ResilAI protects your data, handles authentication,
                    and ensures tenant isolation.
                </p>
            </div>

            {/* Authentication */}
            <section id="authentication">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                        <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        Authentication
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        ResilAI uses Firebase Authentication for secure user identity management.
                    </p>

                    <ul className="space-y-3">
                        {[
                            { title: 'Email/Password Authentication', desc: 'Secure credential-based login with password hashing' },
                            { title: 'Social Providers', desc: 'Optional Google, Microsoft, and GitHub OAuth integration' },
                            { title: 'MFA Support', desc: 'Multi-factor authentication available for enhanced security' },
                            { title: 'Session Management', desc: 'JWT tokens with configurable expiration and refresh' },
                            { title: 'Demo Mode', desc: 'Run assessments without authentication for evaluation' },
                        ].map((item) => (
                            <li key={item.title} className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                                <div>
                                    <span className="font-medium text-gray-900 dark:text-gray-100">{item.title}</span>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">{item.desc}</p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </section>

            {/* Tenant Isolation */}
            <section id="isolation">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                        <Database className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        Tenant Isolation
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        All data is strictly isolated by organization to prevent cross-tenant access.
                    </p>

                    <div className="grid sm:grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Organization Scoping</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Every assessment, finding, and report is scoped to a specific organization ID.
                            </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Role-Based Access</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Users can only access organizations they've been explicitly granted access to.
                            </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">API Enforcement</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                All API endpoints validate organization membership before returning data.
                            </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Audit Logging</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Access attempts are logged for security monitoring and compliance.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Data Storage */}
            <section id="storage">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                        <Database className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        Data Storage
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        ResilAI stores data securely in Google Cloud infrastructure.
                    </p>

                    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Data Type</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Storage</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Encryption</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {[
                                    { type: 'User Accounts', storage: 'Firebase Auth', encryption: 'At rest & in transit' },
                                    { type: 'Organizations', storage: 'Firestore', encryption: 'At rest & in transit' },
                                    { type: 'Assessments', storage: 'Firestore', encryption: 'At rest & in transit' },
                                    { type: 'PDF Reports', storage: 'Cloud Storage', encryption: 'At rest & in transit' },
                                ].map((row) => (
                                    <tr key={row.type}>
                                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{row.type}</td>
                                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{row.storage}</td>
                                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{row.encryption}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* Data Retention */}
            <section id="retention">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                        <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        Data Retention
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <ul className="space-y-3 text-gray-600 dark:text-gray-400">
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Assessment data is retained until explicitly deleted by the user</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Users can request data export or deletion at any time</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Deleted organizations and their data are permanently removed</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Demo mode assessments are stored locally and not persisted to backend</span>
                        </li>
                    </ul>
                </div>
            </section>

            {/* Privacy */}
            <section id="privacy">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                        <Eye className="w-6 h-6 text-red-600 dark:text-red-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        Privacy
                    </h2>
                </div>

                <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <ul className="space-y-3 text-gray-600 dark:text-gray-400">
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>No assessment data is shared with third parties</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Anonymized analytics may be collected for product improvement (opt-out available)</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>AI report generation uses Google Gemini with data not retained for training</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                            <span>Self-hosted deployment option for maximum data control</span>
                        </li>
                    </ul>
                </div>
            </section>
        </div>
    );
}

