import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { clsx } from 'clsx';
import {
    BookOpen,
    BarChart3,
    Shield,
    Lock,
    Code,
    Menu,
    X,
    ChevronRight,
    ExternalLink,
} from 'lucide-react';
import { Footer } from './Footer';
import ThemeToggle from '../ui/ThemeToggle';

interface NavItem {
    name: string;
    href: string;
    icon: typeof BookOpen;
}

const docsNavigation: NavItem[] = [
    { name: 'Overview', href: '/docs', icon: BookOpen },
    { name: 'Methodology', href: '/docs/methodology', icon: BarChart3 },
    { name: 'Frameworks', href: '/docs/frameworks', icon: Shield },
    { name: 'Security', href: '/docs/security', icon: Lock },
    { name: 'API Reference', href: '/docs/api', icon: Code },
];

export default function DocsLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    return (
        <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-gray-900/60 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar - Off-white with blue accents */}
            <aside
                className={clsx(
                    'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col shadow-sm',
                    'transform transition-transform duration-200 ease-in-out lg:translate-x-0',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}
            >
                {/* Logo */}
                <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200 dark:border-slate-800 shrink-0">
                    <Link to="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-sm">
                            <Shield className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-lg font-semibold text-slate-800 dark:text-slate-100">ResilAI</span>
                    </Link>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden p-1 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                    <div className="mb-3 px-3">
                        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Documentation
                        </span>
                    </div>
                    {docsNavigation.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                onClick={() => setSidebarOpen(false)}
                                className={clsx(
                                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                                    isActive
                                        ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-900/60'
                                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                                )}
                            >
                                <item.icon
                                    className={clsx('w-5 h-5', isActive ? 'text-blue-600 dark:text-blue-300' : 'text-slate-400 dark:text-slate-500')}
                                />
                                {item.name}
                            </Link>
                        );
                    })}

                    {/* Separator */}
                    <div className="my-4 border-t border-slate-200 dark:border-slate-800" />

                    {/* Quick links */}
                    <div className="mb-3 px-3">
                        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Quick Links
                        </span>
                    </div>
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
                    >
                        <ChevronRight className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                        Go to Dashboard
                    </Link>
                    <a
                        href="https://www.github.com/purvanshbhatt/AIRS"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
                    >
                        <ExternalLink className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                        GitHub Repository
                    </a>
                </nav>
            </aside>

            {/* Main content wrapper */}
            <div className="flex-1 flex flex-col lg:ml-64">
                {/* Top header */}
                <header className="sticky top-0 z-30 flex items-center h-16 px-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 lg:px-6 shrink-0 shadow-sm">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden p-2 -ml-2 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    {/* Breadcrumb */}
                    <div className="hidden lg:flex items-center gap-2 text-sm">
                        <Link to="/" className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">
                            Home
                        </Link>
                        <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                        <Link to="/docs" className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">
                            Docs
                        </Link>
                        {location.pathname !== '/docs' && (
                            <>
                                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                                <span className="text-slate-800 dark:text-slate-100 font-medium">
                                    {docsNavigation.find((n) => n.href === location.pathname)?.name || 'Page'}
                                </span>
                            </>
                        )}
                    </div>

                    <div className="flex-1" />

                    {/* Right side actions */}
                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <Link
                            to="/assessment/new"
                            className="hidden sm:inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all shadow-sm"
                        >
                            Start Assessment
                        </Link>
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 p-4 lg:p-8 bg-slate-50 dark:bg-slate-950">
                    <div className="max-w-4xl mx-auto">
                        <Outlet />
                    </div>
                </main>

                {/* Footer */}
                <Footer />
            </div>
        </div>
    );
}

