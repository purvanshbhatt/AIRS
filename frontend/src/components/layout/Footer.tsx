import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Github, FileText, Lock, Shield, Activity } from 'lucide-react';
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

    return (
        <footer className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-4 lg:px-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
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

                <p className="text-xs text-gray-400 dark:text-gray-500">
                    ResilAI Public Beta | Aligned to CIS | NIST | OWASP | © 2026 ResilAI
                    {systemStatus ? ` | v${systemStatus.version || 'dev'} (${systemStatus.environment})` : ''}
                </p>
            </div>
        </footer>
    );
}

export default Footer;
