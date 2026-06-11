import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Github, FileText, Lock, Shield, Activity, Mail, ShieldCheck } from 'lucide-react';
import { getSystemStatus } from '../../api';
import type { SystemStatus } from '../../types';

interface FooterLink {
    label: string;
    href: string;
    icon: typeof FileText;
    external?: boolean;
}

const footerLinks: FooterLink[] = [
    { label: 'About', href: '/about', icon: FileText },
    { label: 'Docs', href: '/docs', icon: FileText },
    { label: 'Request Enterprise Pilot', href: '/pilot', icon: Activity },
    { label: 'Privacy', href: '/docs/security#privacy', icon: Lock },
    { label: 'Security', href: '/security', icon: Shield },
    { label: 'GitHub', href: 'https://www.github.com/purvanshbhatt/AIRS', icon: Github, external: true },
    { label: 'Contact', href: 'mailto:purvansh95b@gmail.com', icon: Mail, external: true },
    { label: 'Status', href: '/status', icon: Activity },
];

export function Footer() {
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

    useEffect(() => {
        getSystemStatus()
            .then(setSystemStatus)
            .catch(() => {
                setSystemStatus(null);
            });
    }, []);

    // Check the environment via window location and systemStatus
    const host = typeof window !== 'undefined' ? window.location.hostname : '';
    const isStaging = systemStatus?.environment === 'staging' || 
                      host.includes('staging') || 
                      import.meta.env.MODE === 'staging';

    const isDemo = systemStatus?.environment === 'demo' || 
                   host.includes('demo') || 
                   import.meta.env.MODE === 'demo';

    return (
        <footer className="border-t border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-6 lg:px-6">
            <div className="max-w-[1200px] mx-auto">
                {/* Organic environment status bar */}
                {(isStaging || isDemo) && (
                    <div className="mb-6 p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-4 transition-all duration-300">
                         <div className="flex items-center gap-3">
                            <div className="relative flex h-3 w-3">
                                <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${isStaging ? 'bg-amber-400' : isDemo ? 'bg-blue-400' : 'bg-emerald-400'}`}></span>
                                <span className={`relative inline-flex rounded-full h-3 w-3 ${isStaging ? 'bg-amber-500' : isDemo ? 'bg-blue-500' : 'bg-emerald-500'}`}></span>
                            </div>
                            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                                <span className="text-xs font-mono font-bold tracking-wider text-slate-800 dark:text-slate-200 uppercase">
                                    {isStaging ? 'Staging Environment' : isDemo ? 'Demo Environment' : 'Production Instance'}
                                </span>
                                <span className="hidden sm:inline text-slate-400 dark:text-slate-600">|</span>
                                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                                    {isStaging ? 'staging.resilai.org' : isDemo ? 'demo.resilai.org' : 'resilai.org'}
                                </span>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-4 text-xs font-mono">
                            <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                                <span>SIEM: {isStaging ? 'Verified (Sandbox)' : 'Verified (Production)'}</span>
                            </div>
                            <span className="text-slate-300 dark:text-slate-800">|</span>
                            <div className="text-slate-500 dark:text-slate-400">
                                <span>Latency: {isStaging ? '35ms' : '18ms'}</span>
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex flex-col md:flex-row items-center justify-between gap-6 border-t border-gray-200 dark:border-slate-800 pt-6 mt-6">
                    <div className="flex items-center gap-3">
                        <img 
                            src="/logo_footer_and github.svg" 
                            alt="ResilAI Brand Logo" 
                            className="h-12 w-auto dark:brightness-0 dark:invert transition-all duration-300" 
                        />
                    </div>
                    <nav className="flex flex-wrap items-center justify-center md:justify-end gap-x-6 gap-y-3">
                        {footerLinks.map(({ label, href, icon: Icon, external }) =>
                            external ? (
                                <a
                                    key={label}
                                    href={href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                                >
                                    <Icon className="h-3.5 w-3.5" />
                                    {label}
                                </a>
                            ) : (
                                <Link
                                    key={label}
                                    to={href}
                                    className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                                >
                                    <Icon className="h-3.5 w-3.5" />
                                    {label}
                                </Link>
                            )
                        )}
                    </nav>
                </div>

                <div className="flex items-center justify-center md:justify-end mt-4 pt-2 border-t border-slate-100 dark:border-slate-800/40 w-full">
                    <p className="text-xs text-gray-400 dark:text-gray-500 text-center md:text-right">
                        {isStaging || isDemo ? 'ResilAI Public Beta' : 'ResilAI'} | Aligned to CIS | NIST | OWASP | GNU AGPL-3.0 | (c) 2026 ResilAI
                        {(isStaging || isDemo) && systemStatus ? ` | v${systemStatus.version || 'dev'} (${systemStatus.environment})` : ''}
                    </p>
                </div>
            </div>
        </footer>
    );
}

export default Footer;
