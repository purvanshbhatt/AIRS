import React from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useAuth } from '../../contexts/AuthContext';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import {
  Calendar,
  RotateCcw,
  FileText,
  AlertTriangle,
  Scale,
  Layers,
  Plug,
  Activity,
  CalendarDays,
  Settings,
  BookOpen,
  ShieldCheck,
  Code2,
  Cpu,
  ShieldAlert,
  LogOut,
  UserCheck,
  FileBarChart,
  X,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

export interface AppSidebarProps {
  mobile?: boolean;
  onClose?: () => void;
}

export function AppSidebar({ mobile = false, onClose }: AppSidebarProps = {}) {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { orgName, isDemo } = useActiveOrg();

  const l1Group: NavGroup = {
    label: 'L1: Executive Briefing',
    items: [
      { label: 'Today', icon: Calendar, path: '/morning-brief' },
      { label: 'Recovery', icon: RotateCcw, path: '/recovery' },
      { label: 'Customer Evidence', icon: FileText, path: '/documents' },
    ],
  };

  const l2Group: NavGroup = {
    label: 'L2: Operations Manager',
    items: [
      { label: 'Needs Attention', icon: AlertTriangle, path: '/needs-attention' },
      { label: 'Governance', icon: Scale, path: '/governance' },
    ],
  };

  const l3Group: NavGroup = {
    label: 'L3: IT & Security',
    items: [
      { label: 'Operations Center', icon: Layers, path: '/operations' },
      { label: 'Tech Stack & Inventory', icon: Cpu, path: '/technology/intelligence' },
      { label: 'Reports', icon: FileBarChart, path: '/reports' },
      { label: 'Connectors', icon: Plug, path: '/connectors' },
      { label: 'Telemetry & Evidence', icon: Activity, path: '/activity' },
      { label: 'Audit Calendar', icon: CalendarDays, path: '/audit' },
      { label: 'Settings', icon: Settings, path: '/settings' },
    ],
  };

  const docsGroup: NavGroup = {
    label: 'Trust & Transparency',
    items: [
      { label: 'Scoring Methodology', icon: BookOpen, path: '/docs/methodology' },
      { label: 'Framework Mappings', icon: ShieldCheck, path: '/docs/frameworks' },
      { label: 'API & Verification', icon: Code2, path: '/docs/api' },
    ],
  };

  const navGroups = [l1Group, l2Group, l3Group, docsGroup];

  const handleSignOut = async () => {
    await signOut();
    navigate('/login', { replace: true });
  };

  const handleExitDemoAndLogin = async () => {
    await signOut();
    navigate('/login', { replace: true });
  };

  return (
    <aside
      className={cn(
        "flex-col py-6 bg-surface-container-low dark:bg-surface-container-low border-r border-outline-variant z-50",
        mobile
          ? "flex h-full w-full relative"
          : "hidden md:flex h-screen w-64 fixed left-0 top-0"
      )}
    >
      {/* Brand Header */}
      <div className="px-6 mb-6 flex items-center justify-between">
        <Link
          to="/morning-brief"
          onClick={onClose}
          className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-lg"
          aria-label="ResilAI Home"
        >
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/15 border border-ready-emerald/30 flex items-center justify-center shadow-lg shadow-ready-emerald/10 group-hover:scale-105 transition-transform shrink-0">
            <ShieldAlert className="w-5 h-5 text-ready-emerald" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-on-surface">ResilAI</h1>
              {isDemo ? (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                  Sandbox
                </span>
              ) : (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase bg-ready-emerald/20 text-ready-emerald border border-ready-emerald/30">
                  Live
                </span>
              )}
            </div>
            <p className="text-[11px] text-on-surface-variant font-medium">Healthcare Readiness</p>
          </div>
        </Link>

        {mobile && (
          <button
            onClick={onClose}
            className="md:hidden p-1.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald"
            aria-label="Close navigation menu"
            title="Close navigation menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-3 overflow-y-auto space-y-6" aria-label="Sidebar Navigation">
        {navGroups.map((group) => (
          <div key={group.label}>
            <h3 className="px-3 text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant/70 mb-2">
              {group.label}
            </h3>
            <ul className="space-y-1">
              {group.items.map((item) => {
                const IconComponent = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald",
                          isActive
                            ? "text-ready-emerald bg-ready-emerald/10 border-r-4 border-ready-emerald shadow-sm font-semibold"
                            : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
                        )
                      }
                    >
                      <IconComponent className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Interactive User Profile & Quick Actions */}
      <div className="px-3 mt-auto pt-3 border-t border-outline-variant/40 space-y-2">
        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-surface-container border border-surface-bright">
          {user?.photoURL ? (
            <img
              src={user.photoURL}
              alt=""
              className="w-9 h-9 rounded-full object-cover border border-ready-emerald/40 shrink-0"
            />
          ) : (
            <div className="w-9 h-9 rounded-full bg-ready-emerald/20 border border-ready-emerald/40 flex items-center justify-center text-ready-emerald font-bold text-xs shrink-0">
              {(user?.displayName || user?.email || (isDemo ? 'D' : 'U')).charAt(0).toUpperCase()}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-on-surface truncate">
              {user?.displayName || (isDemo ? 'Dr. Evelyn Reed' : (user?.email?.split('@')[0] || 'User'))}
            </p>
            <p className="text-[10px] text-on-surface-variant truncate font-mono">
              {orgName}
            </p>
          </div>
          <button
            onClick={() => {
              onClose?.();
              handleSignOut();
            }}
            className="p-1.5 hover:bg-surface-container-highest rounded-lg text-on-surface-variant hover:text-critical-red transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald"
            aria-label="Sign Out"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

        {/* Demo Mode Notice & Exit Button */}
        {isDemo ? (
          <button
            onClick={() => {
              onClose?.();
              handleExitDemoAndLogin();
            }}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 bg-ready-emerald/15 hover:bg-ready-emerald hover:text-on-primary-container text-ready-emerald text-[11px] font-semibold rounded-lg border border-ready-emerald/30 transition-all shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald"
            aria-label="Sign In to Live Workspace"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Sign In to Live Workspace</span>
          </button>
        ) : (
          <div className="px-2 text-center">
            <span className="text-[10px] text-on-surface-variant font-mono">
              Deterministic Verification Active
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}
