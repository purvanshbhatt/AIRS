import { useState, ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  ClipboardList,
  Building2,
  FileText,
  Settings,
  SlidersHorizontal,
  BarChart3,
  Menu,
  X,
  ChevronRight,
  Shield,
  LogOut,
  BookOpen,
  Activity,
  Info,
  ShieldCheck,
  Calendar,
  Cpu,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Footer } from './Footer';
import ThemeToggle from '../ui/ThemeToggle';

interface NavItem {
  name: string;
  href: string;
  icon: typeof LayoutDashboard;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Assessments', href: '/dashboard/assessments', icon: ClipboardList },
  { name: 'Results', href: '/dashboard/reports', icon: FileText },
  { name: 'Integrations', href: '/dashboard/integrations', icon: Settings },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Organizations', href: '/dashboard/organizations', icon: Building2 },
  { name: 'Governance', href: '/dashboard/governance', icon: ShieldCheck },
  { name: 'Audit Calendar', href: '/dashboard/audit-calendar', icon: Calendar },
  { name: 'Tech Stack', href: '/dashboard/tech-stack', icon: Cpu },
  { name: 'Settings', href: '/dashboard/settings', icon: SlidersHorizontal },
  { name: 'Status', href: '/status', icon: Activity },
  { name: 'About', href: '/about', icon: Info },
  { name: 'Security', href: '/security', icon: Shield },
  { name: 'Docs', href: '/docs', icon: BookOpen },
];

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut, isConfigured } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const displayName = user?.displayName || user?.email?.split('@')[0] || 'User';
  const displayEmail = user?.email || 'Not signed in';
  const initials = displayName.charAt(0).toUpperCase();

  const isNavItemActive = (href: string, pathname: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/dashboard/';
    }
    if (href === '/dashboard/assessments') {
      return pathname === href || pathname.startsWith('/dashboard/assessment/');
    }
    if (href === '/dashboard/reports') {
      return pathname === href || pathname.startsWith('/dashboard/results/');
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const activeNavItem =
    navigation.find((item) => isNavItemActive(item.href, location.pathname))?.name || 'Page';

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
          {navigation.map((item) => {
            const isActive = isNavItemActive(item.href, location.pathname);
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
        </nav>

        {/* Footer - User info and logout */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 shrink-0">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800/60">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">{initials}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">{displayName}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{displayEmail}</p>
            </div>
          </div>
          
          {(user || isConfigured) && (
            <button
              onClick={handleSignOut}
              className="mt-2 w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign out
            </button>
          )}
        </div>
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
            {location.pathname !== '/' && (
              <>
                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className="text-slate-800 dark:text-slate-100 font-medium">{activeNavItem}</span>
              </>
            )}
          </div>

          <div className="flex-1" />
          <ThemeToggle />
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6 bg-slate-50 dark:bg-slate-950">{children}</main>
        <Footer />
      </div>
    </div>
  );
}

