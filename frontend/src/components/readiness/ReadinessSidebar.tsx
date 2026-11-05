import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Zap, ShieldAlert, Activity, Settings } from 'lucide-react';
import { cn } from '../../lib/utils';

export function ReadinessSidebar() {
  const navItems = [
    { label: 'Today', icon: LayoutDashboard, path: '/readiness' },
    { label: 'Needs Attention', icon: Zap, path: '/readiness/actions' },
    { label: 'Recovery Readiness', icon: ShieldAlert, path: '/readiness/continuity' },
    { label: 'Activity', icon: Activity, path: '/readiness/activity' },
    { label: 'Settings', icon: Settings, path: '/readiness/settings' },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-slate-50/50 hidden md:flex flex-col h-full">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-slate-900 flex items-center justify-center">
            <span className="text-white text-xs font-black">R</span>
          </div>
          ResilAI
        </h1>
      </div>

      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/readiness'}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
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
      </nav>
      
      <div className="p-4 mt-auto">
        <div className="px-3 py-3 rounded-xl bg-blue-50/50 border border-blue-100/50">
          <p className="text-xs font-medium text-blue-900">Readiness Engine Active</p>
          <p className="text-[11px] text-blue-600 mt-0.5">Continuously monitoring systems</p>
        </div>
      </div>
    </aside>
  );
}
