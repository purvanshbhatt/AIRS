import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
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
    { name: 'Governance Engine', href: '/docs/governance', icon: Shield },
    { name: 'Methodology', href: '/docs/methodology', icon: BarChart3 },
    { name: 'Frameworks', href: '/docs/frameworks', icon: Shield },
    { name: 'Security', href: '/docs/security', icon: Lock },
    { name: 'API Reference', href: '/docs/api', icon: Code },
];

export default function DocsLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    return (
        <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
            {/* Mobile sidebar drawer */}
            <AnimatePresence>
                {sidebarOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
                            onClick={() => setSidebarOpen(false)}
                        />

                        {/* Drawer */}
                        <motion.aside
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                            className="fixed left-0 z-50 w-72 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex flex-col shadow-2xl lg:hidden"
                            style={{
                                top: 'var(--banner-height, 0px)',
                                height: 'calc(100vh - var(--banner-height, 0px))',
                            }}
                        >
                            {/* Logo */}
                             <div className="flex items-center justify-between h-16 px-5 border-b border-slate-200 dark:border-slate-800 shrink-0">
                                 <Link to="/" className="flex items-center">
                                     <img src="/logo_header.svg" alt="ResilAI Logo" className="h-10 w-auto dark:brightness-0 dark:invert transition-all duration-300" />
                                 </Link>
                                <button
                                    onClick={() => setSidebarOpen(false)}
                                    className="p-1.5 rounded-full text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Navigation */}
                            <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
                                <div className="mb-4 px-3">
                                    <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-mono">
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
                                                'flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition-all relative overflow-hidden',
                                                isActive
                                                    ? 'bg-blue-600/10 dark:bg-blue-400/5 text-blue-700 dark:text-blue-400 border border-blue-500/20'
                                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200'
                                            )}
                                        >
                                            <item.icon
                                                className={clsx('w-5 h-5', isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500')}
                                            />
                                            {item.name}
                                            {isActive && (
                                                <span className="absolute right-0 top-1/4 bottom-1/4 w-1 bg-blue-600 dark:bg-blue-400 rounded-l" />
                                            )}
                                        </Link>
                                    );
                                })}

                                <div className="my-6 border-t border-slate-200 dark:border-slate-800" />

                                <div className="mb-4 px-3">
                                    <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-mono">
                                        Quick Links
                                    </span>
                                </div>
                                <Link
                                    to="/dashboard"
                                    className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
                                >
                                    <ChevronRight className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                                    Go to Dashboard
                                </Link>
                                <a
                                    href="https://www.github.com/purvanshbhatt/AIRS"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
                                >
                                    <ExternalLink className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                                    GitHub Repository
                                </a>
                            </nav>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>

            {/* Desktop Sidebar */}
            <aside 
                className="hidden lg:flex fixed left-0 z-40 w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex-col shadow-sm"
                style={{
                    top: 'var(--banner-height, 0px)',
                    height: 'calc(100vh - var(--banner-height, 0px))',
                }}
            >
                {/* Logo */}
                 <div className="flex items-center h-16 px-6 border-b border-slate-200 dark:border-slate-800 shrink-0">
                     <Link to="/" className="flex items-center">
                         <img src="/logo_header.svg" alt="ResilAI Logo" className="h-10 w-auto dark:brightness-0 dark:invert transition-all duration-300" />
                     </Link>
                 </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
                    <div className="mb-4 px-3">
                        <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-mono">
                            Documentation
                        </span>
                    </div>
                    {docsNavigation.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                className={clsx(
                                    'flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition-all relative overflow-hidden group',
                                    isActive
                                        ? 'bg-blue-600/10 dark:bg-blue-400/5 text-blue-700 dark:text-blue-450 border border-blue-500/20'
                                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200'
                                )}
                            >
                                <item.icon
                                    className={clsx('w-5 h-5 transition-transform group-hover:scale-105', isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500')}
                                />
                                {item.name}
                                {isActive && (
                                    <span className="absolute right-0 top-1/4 bottom-1/4 w-1 bg-blue-600 dark:bg-blue-400 rounded-l" />
                                )}
                            </Link>
                        );
                    })}

                    <div className="my-6 border-t border-slate-200 dark:border-slate-800" />

                    <div className="mb-4 px-3">
                        <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-mono">
                            Quick Links
                        </span>
                    </div>
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
                    >
                        <ChevronRight className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                        Go to Dashboard
                    </Link>
                    <a
                        href="https://www.github.com/purvanshbhatt/AIRS"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
                    >
                        <ExternalLink className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                        GitHub Repository
                    </a>
                </nav>
            </aside>

            {/* Main content wrapper */}
            <div className="flex-1 flex flex-col lg:ml-64">
                {/* Top header */}
                <header className="sticky top-0 z-30 flex items-center h-16 px-4 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 lg:px-6 shrink-0 shadow-sm backdrop-blur-sm">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden p-2 -ml-2 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                        aria-label="Open sidebar"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    {/* Breadcrumb */}
                    <div className="hidden lg:flex items-center gap-2 text-sm">
                        <Link to="/" className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 font-medium">
                            Home
                        </Link>
                        <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                        <Link to="/docs" className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 font-medium">
                            Docs
                        </Link>
                        {location.pathname !== '/docs' && (
                            <>
                                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                                <span className="text-slate-800 dark:text-slate-100 font-bold">
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
                            to="/dashboard"
                            className="hidden sm:inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-semibold rounded-xl hover:from-blue-600 hover:to-cyan-600 transition-all shadow-sm shadow-blue-500/10"
                        >
                            Open Dashboard
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

