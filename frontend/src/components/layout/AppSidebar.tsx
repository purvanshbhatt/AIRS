import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Zap, 
  ShieldAlert, 
  History,
  Users,
  Laptop,
  Database,
  Mail,
  Network,
  Cloud,
  Cpu,
  Cable,
  Activity,
  ShieldCheck,
  Settings
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface NavGroup {
  label: string;
  items: {
    label: string;
    icon: React.ElementType;
    path: string;
  }[];
}

export function AppSidebar() {
  const navGroups: NavGroup[] = [
    {
      label: 'Morning Operations',
      items: [
        { label: 'Morning Brief', icon: LayoutDashboard, path: '/morning-brief' },
        { label: 'Needs Attention', icon: Zap, path: '/needs-attention' },
        { label: 'Recovery', icon: ShieldAlert, path: '/recovery' },
        { label: 'Yesterday', icon: History, path: '/yesterday' },
      ]
    },
    {
      label: 'Technology Operations',
      items: [
        { label: 'Identity', icon: Users, path: '/identity' },
        { label: 'Devices', icon: Laptop, path: '/devices' },
        { label: 'Backups', icon: Database, path: '/backups' },
        { label: 'Email', icon: Mail, path: '/email' },
        { label: 'Network', icon: Network, path: '/network' },
        { label: 'Cloud', icon: Cloud, path: '/cloud' },
        { label: 'AI', icon: Cpu, path: '/ai' },
      ]
    },
    {
      label: 'Platform',
      items: [
        { label: 'Connectors', icon: Cable, path: '/connectors' },
        { label: 'Activity', icon: Activity, path: '/activity' },
        { label: 'Audit', icon: ShieldCheck, path: '/audit' },
        { label: 'Settings', icon: Settings, path: '/settings' },
      ]
    }
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-slate-50/80 backdrop-blur-xl hidden md:flex flex-col h-full shrink-0">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-slate-900 flex items-center justify-center">
            <span className="text-white text-xs font-black">R</span>
          </div>
          ResilAI
        </h1>
      </div>

      <nav className="flex-1 px-4 overflow-y-auto space-y-8 pb-8">
        {navGroups.map((group) => (
          <div key={group.label}>
            <h3 className="px-3 text-xs font-semibold text-slate-400 tracking-wider mb-2">
              {group.label}
            </h3>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive 
                        ? "bg-white text-slate-900 shadow-sm border border-slate-200/60" 
                        : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 border border-transparent"
                    )
                  }
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
      
      <div className="p-4 mt-auto border-t border-slate-200/60">
        <div className="px-3 py-3 rounded-xl bg-emerald-50/50 border border-emerald-100/50 flex items-start gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 animate-pulse shrink-0" />
          <div>
            <p className="text-xs font-medium text-emerald-900">Engine Active</p>
            <p className="text-[11px] text-emerald-600 mt-0.5">Systems continuously monitored</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
