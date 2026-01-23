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
import { ThemeToggle } from '../ui/ThemeToggle';
import { Footer } from './Footer';

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
        <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={clsx(
                    'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col transition-colors',
                    'transform transition-transform duration-200 ease-in-out lg:translate-x-0',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}
            >
                {/* Logo */}
                <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
                    <Link to="/" className="flex items-center gap-3">
                        <img src="/airs-logo.png" alt="AIRS" className="h-8 w-auto" />
                    </Link>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden p-1 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                    <div className="mb-3 px-3">
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
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
                                        ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
                                )}
                            >
                                <item.icon
                                    className={clsx('w-5 h-5', isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500')}
                                />
                                {item.name}
                            </Link>
                        );
                    })}

                    {/* Separator */}
                    <div className="my-4 border-t border-gray-200 dark:border-gray-700" />

                    {/* Quick links */}
                    <div className="mb-3 px-3">
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Quick Links
                        </span>
                    </div>
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                        Go to Dashboard
                    </Link>
                    <a
                        href="https://github.com/purvanshbhatt/AIRS"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                        <ExternalLink className="w-5 h-5 text-gray-400" />
                        GitHub Repository
                    </a>
                </nav>
            </aside>

            {/* Main content wrapper */}
            <div className="flex-1 flex flex-col lg:ml-64">
                {/* Top header */}
                <header className="sticky top-0 z-30 flex items-center h-16 px-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 lg:px-6 shrink-0 transition-colors">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden p-2 -ml-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    {/* Breadcrumb */}
                    <div className="hidden lg:flex items-center gap-2 text-sm">
                        <Link to="/" className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                            Home
                        </Link>
                        <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        <Link to="/docs" className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                            Docs
                        </Link>
                        {location.pathname !== '/docs' && (
                            <>
                                <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                                <span className="text-gray-900 dark:text-gray-100 font-medium">
                                    {docsNavigation.find((n) => n.href === location.pathname)?.name || 'Page'}
                                </span>
                            </>
                        )}
                    </div>

                    {/* Spacer */}
                    <div className="flex-1" />

                    {/* Right side actions */}
                    <div className="flex items-center gap-4">
                        <Link
                            to="/assessment/new"
                            className="hidden sm:inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
                        >
                            Start Assessment
                        </Link>
                        <ThemeToggle />
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 p-4 lg:p-8">
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
