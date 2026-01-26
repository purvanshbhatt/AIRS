import { Link } from 'react-router-dom';
import { Github, FileText, Lock, Shield, Activity } from 'lucide-react';

interface FooterLink {
    label: string;
    href: string;
    icon: typeof FileText;
    external?: boolean;
}

const footerLinks: FooterLink[] = [
    { label: 'Docs', href: '/docs', icon: FileText },
    { label: 'Privacy', href: '/docs/security#privacy', icon: Lock },
    { label: 'Security', href: '/docs/security', icon: Shield },
    { label: 'GitHub', href: 'https://github.com', icon: Github, external: true },
    { label: 'Status', href: '/docs/api', icon: Activity },
];

export function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-4 lg:px-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                {/* Links */}
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

                {/* Copyright */}
                <p className="text-xs text-gray-400 dark:text-gray-500">
                    © {currentYear} AIRS. Open source under MIT license.
                </p>
            </div>
        </footer>
    );
}

export default Footer;
